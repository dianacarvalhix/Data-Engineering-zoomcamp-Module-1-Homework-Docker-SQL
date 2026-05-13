
variable "project" {
  description = "Project"
  default        = "project-b31a1c88-103c-4da2-b2c"
}


variable "service_account_email" {
  description = "email"
  default        = "terraform-runner@project-b31a1c88-103c-4da2-b2c.iam.gserviceaccount.com"
}


variable "region" {
  description = "region"
  default        = "europe-west1"
}


variable "zone" {
  description = "zone"
  default        = "europe-west1-b"
}




variable "location" {
  description = "Project Location"
  default        = "EU"
}



variable "bq_dataset_name" {
  description = "My BigQuery dataset name"
  default        = "dataeng_course"
}

variable "gcs_bucket_name" {
  description = "My Storage bucket name"
  default        = "project-b31a1c88-103c-4da2-b2c-terra-bucket"
}



variable "gcs_storage_class" {
  description = "Bucket Storage Class"
  default        = "STANDARD"
}

