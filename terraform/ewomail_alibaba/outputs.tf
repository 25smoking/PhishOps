output "public_ip" {
  value = alicloud_instance.instance.public_ip
}
output "instance_id" {
  value = alicloud_instance.instance.id
}
