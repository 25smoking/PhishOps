resource "tencentcloud_vpc" "vpc" {
  name       = "${var.instance_name}_vpc"
  cidr_block = "10.0.0.0/16"
}

resource "tencentcloud_subnet" "subnet" {
  vpc_id            = tencentcloud_vpc.vpc.id
  name              = "${var.instance_name}_subnet"
  cidr_block        = "10.0.1.0/24"
  availability_zone          = var.availability_zone
}

resource "tencentcloud_security_group" "sg" {
  name = "${var.instance_name}_sg"
}

variable "ewomail_ports" {
  default = ["22", "80", "443", "25", "465", "587", "110", "995", "143", "993", "8000", "8010", "8020"]
}

resource "tencentcloud_security_group_rule" "allow_ewomail_ports" {
  count             = length(var.ewomail_ports)
  security_group_id = tencentcloud_security_group.sg.id
  type              = "ingress"
  cidr_ip           = "0.0.0.0/0"
  ip_protocol       = "TCP"
  policy            = "ACCEPT"
  port_range        = var.ewomail_ports[count.index]
}

# 允许所有出站流量
resource "tencentcloud_security_group_rule" "allow_all_egress" {
  security_group_id = tencentcloud_security_group.sg.id
  type              = "egress"
  cidr_ip           = "0.0.0.0/0"
  ip_protocol       = "TCP"
  policy            = "ACCEPT"
}

resource "tencentcloud_security_group_rule" "allow_udp_egress" {
  security_group_id = tencentcloud_security_group.sg.id
  type              = "egress"
  cidr_ip           = "0.0.0.0/0"
  ip_protocol       = "UDP"
  policy            = "ACCEPT"
}

resource "tencentcloud_key_pair" "key" {
  key_name   = "${replace(var.instance_name, "-", "_")}_key"
  public_key = var.ssh_public_key
}

data "tencentcloud_images" "centos" {
  image_type       = ["PUBLIC_IMAGE"]
  image_name_regex = "CentOS 7\\.[689] .*64"
}

resource "tencentcloud_instance" "instance" {
  instance_name              = var.instance_name
  availability_zone          = var.availability_zone
  image_id                   = data.tencentcloud_images.centos.images[0].image_id
  instance_type              = var.instance_type
  system_disk_type           = "CLOUD_PREMIUM"
  system_disk_size           = 50
  allocate_public_ip         = true
  internet_max_bandwidth_out = 100
  internet_charge_type       = "TRAFFIC_POSTPAID_BY_HOUR"
  
  vpc_id                     = tencentcloud_vpc.vpc.id
  subnet_id                  = tencentcloud_subnet.subnet.id
  security_groups            = [tencentcloud_security_group.sg.id]
  
  # 使用user_data配置SSH公钥
  # Use key_ids for native key injection
  key_ids = [tencentcloud_key_pair.key.id]
}

output "public_ip" {
  value = tencentcloud_instance.instance.public_ip
}

output "instance_id" {
  value = tencentcloud_instance.instance.id
}
