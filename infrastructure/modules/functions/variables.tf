variable "resource_group_name"      { type = string }
variable "location"                  { type = string }
variable "prefix"                    { type = string }
variable "storage_account_name"      { type = string }
variable "storage_account_access_key" {
  type      = string
  sensitive = true
}
variable "storage_connection_string" {
  type      = string
  sensitive = true
}
variable "speech_key" {
  type      = string
  sensitive = true
}
variable "speech_region"             { type = string }
variable "nlp_model_url" {
  type    = string
  default = ""
}
variable "risk_engine_url" {
  type    = string
  default = ""
}
variable "retrain_secret" {
  type      = string
  sensitive = true
  default   = ""
}
variable "tags"                      { type = map(string) }
