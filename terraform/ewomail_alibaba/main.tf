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

variable "ewomail_ports" {
  default = ["22/22", "80/80", "443/443", "25/25", "465/465", "587/587", "110/110", "995/995", "143/143", "993/993", "8000/8000", "8010/8010", "8020/8020"]
}

resource "alicloud_security_group_rule" "allow_ewomail_ports" {
  count             = length(var.ewomail_ports)
  type              = "ingress"
  ip_protocol       = "tcp"
  policy            = "accept"
  port_range        = var.ewomail_ports[count.index]
  priority          = 1
  security_group_id = alicloud_security_group.sg.id
  cidr_ip           = "0.0.0.0/0"
}


resource "alicloud_key_pair" "key" {
  key_pair_name = "${var.instance_name}-key"
  public_key    = var.ssh_public_key
}

data "alicloud_images" "centos" {
  name_regex = "^centos_7"
  owners     = "system"
  os_type    = "linux"
}

resource "alicloud_instance" "instance" {
  availability_zone = "${var.region}a"
  security_groups   = [alicloud_security_group.sg.id]
  instance_type     = var.instance_type
  system_disk_category = "cloud_efficiency"
  image_id          = data.alicloud_images.centos.images[0].id
  instance_name     = var.instance_name
  vswitch_id        = alicloud_vswitch.vsw.id
  internet_max_bandwidth_out = 100
  key_name          = alicloud_key_pair.key.key_pair_name
}
