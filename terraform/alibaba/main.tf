resource "alicloud_vpc" "vpc" {
  vpc_name   = "${var.instance_name}-vpc"
  cidr_block = "10.0.0.0/16"
}

resource "alicloud_vswitch" "vsw" {
  vpc_id     = alicloud_vpc.vpc.id
  cidr_block = "10.0.1.0/24"
  zone_id    = "${var.region}a"
}

resource "alicloud_security_group" "sg" {
  name   = "${var.instance_name}-sg"
  vpc_id = alicloud_vpc.vpc.id
}

resource "alicloud_security_group_rule" "allow_ssh" {
  type              = "ingress"
  ip_protocol       = "tcp"
  policy            = "accept"
  port_range        = "22/22"
  priority          = 1
  security_group_id = alicloud_security_group.sg.id
  cidr_ip           = "0.0.0.0/0"
}

resource "alicloud_security_group_rule" "allow_phish" {
  type              = "ingress"
  ip_protocol       = "tcp"
  policy            = "accept"
  port_range        = "80/80"
  priority          = 1
  security_group_id = alicloud_security_group.sg.id
  cidr_ip           = "0.0.0.0/0"
}

resource "alicloud_security_group_rule" "allow_admin" {
  type              = "ingress"
  ip_protocol       = "tcp"
  policy            = "accept"
  port_range        = "3333/3333"
  priority          = 1
  security_group_id = alicloud_security_group.sg.id
  cidr_ip           = "0.0.0.0/0"
}

resource "alicloud_key_pair" "key" {
  key_pair_name = "${var.instance_name}-key"
  public_key    = var.ssh_public_key
}

resource "alicloud_instance" "instance" {
  availability_zone = "${var.region}a"
  security_groups   = [alicloud_security_group.sg.id]
  instance_type     = var.instance_type
  system_disk_category = "cloud_efficiency"
  image_id          = "ubuntu_22_04_x64_20G_alibase_20230614.vhd"
  instance_name     = var.instance_name
  vswitch_id        = alicloud_vswitch.vsw.id
  internet_max_bandwidth_out = 100
  key_name          = alicloud_key_pair.key.key_pair_name
}
