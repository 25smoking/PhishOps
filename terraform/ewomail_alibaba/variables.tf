variable "access_key" {
  description = "阿里云 Access Key ID"
}
variable "secret_key" {
  description = "阿里云 Access Key Secret"
}
variable "region" {
  description = "部署区域 (例如: cn-shanghai)"
  default     = "cn-shanghai"
}
variable "instance_type" {
  description = "实例规格 (默认 2核4G)"
  default     = "ecs.c6.large"
}
variable "instance_name" {
  description = "实例名称"
  default     = "gophish-auto"
}
variable "ssh_public_key" {
  description = "SSH 公钥内容"
}
