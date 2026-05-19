variable "resource_group_name"          { type = string }
variable "location"                    { type = string }
variable "prefix"                      { type = string }
variable "acr_login_server"            { type = string }
variable "acr_admin_username"          { type = string }
variable "acr_admin_password" {
  type      = string
  sensitive = true
}
variable "azure_speech_key" {
  type      = string
  sensitive = true
}
variable "azure_speech_region"         { type = string }
variable "azure_blob_connection_string" {
  type      = string
  sensitive = true
}
variable "retrain_secret" {
  type      = string
  sensitive = true
}
variable "tags"                        { type = map(string) }
