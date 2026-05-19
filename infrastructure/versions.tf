terraform {
  required_version = ">= 1.7.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Remote state stored in Azure Blob (bootstrap this once manually — see README)
  backend "azurerm" {
    resource_group_name  = "ppd-tfstate-rg"
    storage_account_name = "ppdtfstate"
    container_name       = "tfstate"
    key                  = "ppd.terraform.tfstate"
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
}
