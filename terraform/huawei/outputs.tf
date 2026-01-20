output "public_ip" {
  value = huaweicloud_vpc_eip.eip.address
}
output "instance_id" {
  value = huaweicloud_compute_instance.instance.id
}
