variable "secret_id" {
  description = "腾讯云 Secret ID"
}
variable "secret_key" {
  description = "腾讯云 Secret Key"
}
variable "region" {
  description = "部署区域 (例如: ap-guangzhou)"
  default     = "ap-guangzhou"
}
variable "instance_type" {
  description = "实例规格 (默认 2核4G)"
  default     = "SA2.MEDIUM4"  # 标准型SA2，兼容性更好
}
variable "instance_name" {
  description = "实例名称"
  default     = "gophish-auto"
}
variable "ssh_public_key" {
  description = "SSH 公钥内容"
  default     = "dummy-key"  # destroy时不需要真实的公钥
}
variable "availability_zone" {
  description = "可用区"
  default     = "ap-hongkong-2" # 提供一个默认值，但允许覆盖
}
