resource "huaweicloud_vpc" "vpc" {
  name = "${var.instance_name}-vpc"
  cidr = "10.0.0.0/16"
}

resource "huaweicloud_vpc_subnet" "subnet" {
  name       = "${var.instance_name}-subnet"
  cidr       = "10.0.1.0/24"
  gateway_ip = "10.0.1.1"
  vpc_id     = huaweicloud_vpc.vpc.id
}

resource "huaweicloud_networking_secgroup" "sg" {
  name = "${var.instance_name}-sg"
}

resource "huaweicloud_networking_secgroup_rule" "allow_ssh" {
  security_group_id = huaweicloud_networking_secgroup.sg.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
}

resource "huaweicloud_networking_secgroup_rule" "allow_web" {
  security_group_id = huaweicloud_networking_secgroup.sg.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
}

resource "huaweicloud_networking_secgroup_rule" "allow_admin" {
  security_group_id = huaweicloud_networking_secgroup.sg.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 3333
  port_range_max    = 3333
  remote_ip_prefix  = "0.0.0.0/0"
}

resource "huaweicloud_kps_keypair" "key" {
  name       = "${var.instance_name}-key"
  public_key = var.ssh_public_key
}

resource "huaweicloud_compute_instance" "instance" {
  name            = var.instance_name
  image_name      = "Ubuntu 22.04 server 64bit"
  flavor_name     = var.instance_type
  key_pair        = huaweicloud_kps_keypair.key.name
  security_group_ids = [huaweicloud_networking_secgroup.sg.id]
  
  network {
    uuid = huaweicloud_vpc_subnet.subnet.id
  }
}

resource "huaweicloud_vpc_eip" "eip" {
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name        = "${var.instance_name}-bw"
    size        = 100
    share_type  = "PER"
    charge_mode = "traffic"
  }
}

resource "huaweicloud_compute_eip_associate" "associated" {
  public_ip   = huaweicloud_vpc_eip.eip.address
  instance_id = huaweicloud_compute_instance.instance.id
}
