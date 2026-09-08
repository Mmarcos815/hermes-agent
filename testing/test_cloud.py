#!/usr/bin/env python3
"""
test_cloud.py — Test cloud VPS engine against LocalStack patterns.

Tests the HighRamCapacityPlanner and PrivateCloudVPSManager using mock
data that mirrors LocalStack-style cloud resource provisioning patterns.

Run: pytest testing/test_cloud.py -v
"""

import sys
import os
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bionic_cloud_vps_engine import HighRamCapacityPlanner, PrivateCloudVPSManager


# ── Mock Data: LocalStack-style resource vectors ───────────────────────────

MOCK_HOST_CONFIG = {
    "physical_ram_gb": 128,
    "numa_nodes": 2,
    "hugepage_size_mb": 2,
}

MOCK_VPS_LARGE = {
    "name": "bionic-model-runner-01",
    "vcpus": 16,
    "ram_gb": 64,
    "disk_gb": 250,
    "os_image": "ubuntu-24.04-ai-hardened",
    "enable_zram": True,
}

MOCK_VPS_MEDIUM = {
    "name": "bionic-recon-swarm-02",
    "vcpus": 8,
    "ram_gb": 32,
    "disk_gb": 100,
    "os_image": "kali-rolling-cloud",
    "enable_zram": True,
}

MOCK_VPS_SMALL = {
    "name": "bionic-monitor-03",
    "vcpus": 4,
    "ram_gb": 8,
    "disk_gb": 50,
    "os_image": "debian-12-minimal",
    "enable_zram": False,
}

MOCK_RESOURCE_EXHAUST = {
    "name": "bionic-exhaust-test",
    "vcpus": 64,
    "ram_gb": 256,
    "disk_gb": 1000,
    "os_image": "fake-image",
    "enable_zram": True,
}


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def planner():
    """Fresh HighRamCapacityPlanner for each test."""
    return HighRamCapacityPlanner(**MOCK_HOST_CONFIG)


@pytest.fixture
def manager():
    """Fresh PrivateCloudVPSManager with default planner."""
    planner = HighRamCapacityPlanner(**MOCK_HOST_CONFIG)
    return PrivateCloudVPSManager(planner)


# ── Test: Memory Layout Calculation ────────────────────────────────────────

class TestMemoryLayout:
    def test_physical_ram_reported(self, planner):
        layout = planner.calculate_memory_layout()
        assert layout["physical_ram_gb"] == 128

    def test_numa_nodes_count(self, planner):
        layout = planner.calculate_memory_layout()
        assert layout["numa_nodes_count"] == 2

    def test_ram_per_numa_node(self, planner):
        layout = planner.calculate_memory_layout()
        assert layout["ram_per_numa_node_gb"] == 64

    def test_host_reservation_applied(self, planner):
        layout = planner.calculate_memory_layout(host_reserved_gb=8)
        assert layout["hypervisor_allocatable_ram_gb"] == 120

    def test_hugepages_calculated(self, planner):
        layout = planner.calculate_memory_layout(host_reserved_gb=8)
        assert layout["hugepages_2mb_count"] == 61440

    def test_zram_multiplier_applied(self, planner):
        layout = planner.calculate_memory_layout(zram_compression_ratio=2.5)
        expected = 120 * 2.5
        assert layout["virtual_effective_memory_capacity_gb"] == expected

    def test_kernel_boot_params(self, planner):
        layout = planner.calculate_memory_layout()
        assert "default_hugepagesz=2M" in layout["kernel_boot_params"]
        assert "hugepages=" in layout["kernel_boot_params"]

    def test_zero_ram_when_fully_reserved(self, planner):
        layout = planner.calculate_memory_layout(host_reserved_gb=200)
        assert layout["hypervisor_allocatable_ram_gb"] == 0


# ── Test: VPS Provisioning ─────────────────────────────────────────────────

class TestVPSProvisioning:
    def test_provision_large_vps(self, manager):
        result = manager.provision_vps(**MOCK_VPS_LARGE)
        assert result["success"] is True
        assert result["instance"]["ram_gb"] == 64

    def test_provision_medium_vps(self, manager):
        result = manager.provision_vps(**MOCK_VPS_MEDIUM)
        assert result["success"] is True
        assert result["instance"]["vcpus"] == 8

    def test_provision_small_vps(self, manager):
        result = manager.provision_vps(**MOCK_VPS_SMALL)
        assert result["success"] is True

    def test_vps_has_uuid(self, manager):
        result = manager.provision_vps(**MOCK_VPS_LARGE)
        assert result["instance"]["vps_id"].startswith("vps-")

    def test_vps_has_mac_address(self, manager):
        result = manager.provision_vps(**MOCK_VPS_LARGE)
        mac = result["instance"]["mac_address"]
        assert mac.startswith("52:54:00:")

    def test_vps_has_tap_interface(self, manager):
        result = manager.provision_vps(**MOCK_VPS_LARGE)
        assert "tap_" in result["instance"]["tap_interface"]

    def test_vps_status_provisioned(self, manager):
        result = manager.provision_vps(**MOCK_VPS_LARGE)
        assert result["instance"]["status"] == "PROVISIONED_RUNNING"


# ── Test: VPS Termination ─────────────────────────────────────────────────

class TestVPSTermination:
    def test_terminate_existing_vps(self, manager):
        result = manager.provision_vps(**MOCK_VPS_LARGE)
        vps_id = result["instance"]["vps_id"]

        term_result = manager.terminate_vps(vps_id)
        assert term_result["success"] is True
        assert term_result["terminated_vps_id"] == vps_id

    def test_terminate_nonexistent_vps(self, manager):
        result = manager.terminate_vps("vps-nonexistent")
        assert result["success"] is False

    def test_terminate_frees_ram(self, manager):
        prov = manager.provision_vps(**MOCK_VPS_LARGE)
        vps_id = prov["instance"]["vps_id"]
        ram_before = manager.total_allocated_ram_gb

        manager.terminate_vps(vps_id)
        assert manager.total_allocated_ram_gb == ram_before - 64

    def test_terminate_frees_vcpus(self, manager):
        prov = manager.provision_vps(**MOCK_VPS_LARGE)
        vps_id = prov["instance"]["vps_id"]

        manager.terminate_vps(vps_id)
        assert manager.total_allocated_vcpus == 0


# ── Test: Resource Limits ─────────────────────────────────────────────────

class TestResourceLimits:
    def test_insufficient_memory_rejected(self, manager):
        result = manager.provision_vps(**MOCK_RESOURCE_EXHAUST)
        assert result["success"] is False
        assert "Insufficient" in result["error"]

    def test_partial_allocation_then_exhaust(self, manager):
        manager.provision_vps(**MOCK_VPS_LARGE)
        manager.provision_vps(**MOCK_VPS_MEDIUM)

        result = manager.provision_vps(
            name="overflow",
            vcpus=1,
            ram_gb=30,
            disk_gb=10,
            os_image="test",
        )
        assert result["success"] is False


# ── Test: Cluster Status ──────────────────────────────────────────────────

class TestClusterStatus:
    def test_empty_cluster(self, manager):
        status = manager.get_cluster_status()
        assert status["active_vps_instances_count"] == 0
        assert status["allocated_ram_gb"] == 0

    def test_single_instance_cluster(self, manager):
        manager.provision_vps(**MOCK_VPS_LARGE)
        status = manager.get_cluster_status()
        assert status["active_vps_instances_count"] == 1
        assert status["allocated_ram_gb"] == 64

    def test_multiple_instances_cluster(self, manager):
        manager.provision_vps(**MOCK_VPS_LARGE)
        manager.provision_vps(**MOCK_VPS_MEDIUM)
        status = manager.get_cluster_status()
        assert status["active_vps_instances_count"] == 2
        assert status["allocated_ram_gb"] == 96
        assert status["free_ram_gb"] == 24

    def test_cluster_lists_instances(self, manager):
        manager.provision_vps(**MOCK_VPS_SMALL)
        status = manager.get_cluster_status()
        assert len(status["instances"]) == 1
        assert status["instances"][0]["name"] == "bionic-monitor-03"


# ── Test: QEMU Launch Command ──────────────────────────────────────────────

class TestQEMULaunch:
    def test_qemu_cmd_contains_cpu(self, manager):
        result = manager.provision_vps(**MOCK_VPS_LARGE)
        cmd = result["instance"]["qemu_launch_command"]
        assert "-smp 16" in cmd

    def test_qemu_cmd_contains_memory(self, manager):
        result = manager.provision_vps(**MOCK_VPS_LARGE)
        cmd = result["instance"]["qemu_launch_command"]
        assert "-m 64G" in cmd

    def test_qemu_cmd_uses_kvm(self, manager):
        result = manager.provision_vps(**MOCK_VPS_LARGE)
        cmd = result["instance"]["qemu_launch_command"]
        assert "accel=kvm" in cmd

    def test_qemu_cmd_has_virtio_net(self, manager):
        result = manager.provision_vps(**MOCK_VPS_LARGE)
        cmd = result["instance"]["qemu_launch_command"]
        assert "virtio-net-pci" in cmd


# ── Test: Cloud-Init Generation ───────────────────────────────────────────

class TestCloudInit:
    def test_cloud_init_has_hostname(self, manager):
        result = manager.provision_vps(**MOCK_VPS_LARGE)
        cloud_init = result["instance"]["cloud_init"]
        assert "bionic-model-runner-01" in cloud_init

    def test_cloud_init_manages_hosts(self, manager):
        result = manager.provision_vps(**MOCK_VPS_LARGE)
        cloud_init = result["instance"]["cloud_init"]
        assert "manage_etc_hosts: true" in cloud_init

    def test_cloud_init_installs_packages(self, manager):
        result = manager.provision_vps(**MOCK_VPS_LARGE)
        cloud_init = result["instance"]["cloud_init"]
        assert "qemu-guest-agent" in cloud_init
