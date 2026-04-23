provider "google" {
  project = "project-b31a1c88-103c-4da2-b2c"
  region  = var.region
  zone    = var.zone
}

data "google_service_account_access_token" "default" {
  provider               = google
  target_service_account = var.service_account_email
  scopes                 = ["https://www.googleapis.com/auth/cloud-platform"]
  lifetime               = "3600s"
}

provider "google" {
  alias        = "impersonated"
  access_token = data.google_service_account_access_token.default.access_token
  project      = var.project
  region       = var.region
  zone         = var.zone
}




resource "google_storage_bucket" "demo-bucket" {
  provider = google.impersonated
  name                        = var.gcs_bucket_name
  location                    = var.location
  force_destroy               = true
  uniform_bucket_level_access = true


  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}




resource "google_bigquery_dataset" "dataeng_course" {
  provider = google.impersonated
  dataset_id = var.bq_dataset_name
  delete_contents_on_destroy =  true
  location                    = var.location

}