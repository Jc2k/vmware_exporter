import datetime
from unittest import mock

import pytest_twisted
import pytz
from pyVmomi import vim

from vmware_exporter.vmware_exporter import VmwareCollector

EPOCH = datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)


@mock.patch('vmware_exporter.vmware_exporter.batch_fetch_properties')
@pytest_twisted.inlineCallbacks
def test_collect_vms(batch_fetch_properties):
    content = mock.Mock()

    boot_time = EPOCH + datetime.timedelta(seconds=60)

    batch_fetch_properties.return_value = {
        'vm-1': {
            'name': 'vm-1',
            'runtime.host': vim.ManagedObject('host-1'),
            'runtime.powerState': 'poweredOn',
            'summary.config.numCpu': 1,
            'runtime.bootTime': boot_time,
        }
    }

    collect_only = {
        'vms': True,
        'vmguests': True,
        'datastores': True,
        'hosts': True,
        'snapshots': True,
    }
    collector = VmwareCollector(
        '127.0.0.1',
        'root',
        'password',
        collect_only,
    )

    inventory = {
        'host-1': {
            'name': 'host-1',
            'dc': 'dc',
            'cluster': 'cluster-1',
        }
    }

    metrics = collector._create_metric_containers()

    collector._labels = {}

    with mock.patch.object(collector, '_vmware_get_vm_perf_manager_metrics'):
        yield collector._vmware_get_vms(content, metrics, inventory)

    assert metrics['vmware_vm_power_state'].samples[0][1] == {
        'vm_name': 'vm-1',
        'host_name': 'host-1',
        'cluster_name': 'cluster-1',
        'dc_name': 'dc',
    }
    assert metrics['vmware_vm_power_state'].samples[0][2] == 1.0

    assert metrics['vmware_vm_boot_timestamp_seconds'].samples[0][1] == {
        'vm_name': 'vm-1',
        'host_name': 'host-1',
        'cluster_name': 'cluster-1',
        'dc_name': 'dc',
    }
    assert metrics['vmware_vm_boot_timestamp_seconds'].samples[0][2] == 60


@mock.patch('vmware_exporter.vmware_exporter.batch_fetch_properties')
def test_collect_datastore(batch_fetch_properties):
    content = mock.Mock()

    batch_fetch_properties.return_value = {
        'datastore-1': {
            'name': 'datastore-1',
            'summary.capacity': 0,
            'summary.freeSpace': 0,
            'host': ['host-1'],
            'vm': ['vm-1'],
            'summary.accessible': True,
            'summary.maintenanceMode': 'normal',
        }
    }

    collect_only = {
        'vms': True,
        'vmguests': True,
        'datastores': True,
        'hosts': True,
        'snapshots': True,
    }
    collector = VmwareCollector(
        '127.0.0.1',
        'root',
        'password',
        collect_only,
    )

    inventory = {
        'datastore-1': {
            'dc': 'dc',
            'ds_cluster': 'ds_cluster',
        }
    }

    metrics = collector._create_metric_containers()
    collector._vmware_get_datastores(content, metrics, inventory)

    assert metrics['vmware_datastore_capacity_size'].samples[0][1] == {
        'ds_name': 'datastore-1',
        'dc_name': 'dc',
        'ds_cluster': 'ds_cluster'
    }
    assert metrics['vmware_datastore_capacity_size'].samples[0][2] == 0.0

    assert metrics['vmware_datastore_maintenance_mode'].samples[0][1] == {
        'ds_name': 'datastore-1',
        'dc_name': 'dc',
        'ds_cluster': 'ds_cluster',
        'mode': 'normal'
    }
    assert metrics['vmware_datastore_maintenance_mode'].samples[0][2] == 1.0

    assert metrics['vmware_datastore_accessible'].samples[0][1] == {
        'ds_name': 'datastore-1',
        'dc_name': 'dc',
        'ds_cluster': 'ds_cluster'
    }
    assert metrics['vmware_datastore_accessible'].samples[0][2] == 1.0
