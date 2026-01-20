variable "access_key" {
  description = "华为云 Access Key"
}
variable "secret_key" {
  description = "华为云 Secret Key"
}
variable "region" {
  description = "部署区域 (例如: cn-north-4)"
  default     = "cn-north-4"
}
variable "instance_type" {
  description = "实例规格 (默认 2核4G)"
  default     = "s6.large.2"
}
variable "instance_name" {
  description = "实例名称"
  default     = "gophish-auto"
}
variable "ssh_public_key" {
  description = "SSH 公钥内容"
}
