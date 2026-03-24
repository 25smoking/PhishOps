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

variable "ewomail_ports" {
  default = [22, 80, 443, 25, 465, 587, 110, 995, 143, 993, 8000, 8010, 8020]
}

resource "huaweicloud_networking_secgroup_rule" "allow_ewomail_ports" {
  count             = length(var.ewomail_ports)
  security_group_id = huaweicloud_networking_secgroup.sg.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = var.ewomail_ports[count.index]
  port_range_max    = var.ewomail_ports[count.index]
  remote_ip_prefix  = "0.0.0.0/0"
}


resource "huaweicloud_kps_keypair" "key" {
  name       = "${var.instance_name}-key"
  public_key = var.ssh_public_key
}

data "huaweicloud_images_image" "centos" {
  name        = "CentOS 7.9 64bit"
  visibility  = "public"
  most_recent = true
}

resource "huaweicloud_compute_instance" "instance" {
  name            = var.instance_name
  image_id        = data.huaweicloud_images_image.centos.id
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
