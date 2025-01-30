import click
import json
import requests
from requests.auth import HTTPBasicAuth

requests.packages.urllib3.disable_warnings()

def authenticate(url, username, password):
    """Authenticate to DNAC and return the token."""
    auth_url = f"{url}/dna/system/api/v1/auth/token"
    try:
        response = requests.post(
            auth_url,
            auth=HTTPBasicAuth(username, password),
            verify=False
        )
        response.raise_for_status()  # Raises an error for bad responses
        token = response.json().get("Token")
        click.echo(f"Authentication successful!")
        return token
    except requests.exceptions.RequestException as e:
        click.echo(f"Authentication failed: {e}")
        return None

def cleanup_pools(token, url, dryrun=False):
    """Cleanup IP pools in Lab 1."""
    if dryrun:
        headers = {"x-auth-token": token, 'content-type': 'application/json'}
        try:
            response = requests.request("GET", url+"/dna/intent/api/v1/reserve-ip-subpool?ignoreInheritedGroups=true", headers=headers, verify=False)
            if response.status_code == 200:
                click.echo("Retrieving list of ip sub pools...")
                pools_dict = {}
                for pool in response.json()["response"]:
                    pools_dict[pool["groupName"]] = pool["id"]

                click.echo("Deleting ip sub pools...")
                for pool_name, pool_id in pools_dict.items():
                    response = requests.request("DELETE", url+"/dna/intent/api/v1/reserve-ip-subpool/" + pool_id, headers=headers, verify=False)
                    if response.status_code == 202:
                        click.echo(f"Deleted IP sub pool: {pool_name}")
                    else:
                        click.echo(f"Failed to delete IP sub pool: {pool_name}. Status Code: {response.status_code}, Response: {response.text}")
            else:
                click.echo(f"Failed to retrieve sub pools. Status Code: {response.status_code}, Response: {response.text}")
        except requests.exceptions.RequestException as e:
            click.echo(f"Failed to cleanup IP sub pools: {e}")

        try:
            response = requests.request("GET", url+"/dna/intent/api/v1/global-pool", headers=headers, verify=False)
            if response.status_code == 200:
                click.echo("Retrieving list of ip pools...")
                pools_dict = {}
                for pool in response.json()["response"]:
                    pools_dict[pool["ipPoolName"]] = pool["id"]

                click.echo("Deleting ip pools...")
                for pool_name, pool_id in pools_dict.items():
                    response = requests.request("DELETE", url+"/dna/intent/api/v1/global-pool/" + pool_id, headers=headers, verify=False)
                    if response.status_code == 202:
                        click.echo(f"Deleted IP pool: {pool_name}")
                    else:
                        click.echo(f"Failed to delete IP pool: {pool_name}. Status Code: {response.status_code}, Response: {response.text}")
            else:
                click.echo(f"Failed to retrieve IP pools. Status Code: {response.status_code}, Response: {response.text}")
        except requests.exceptions.RequestException as e:
            click.echo(f"Failed to cleanup IP pools: {e}")

        click.echo("IP sub pools cleaned up successfully.")
    else:
        click.echo("IP sub pools cleaned up successfully. (dryrun)")
    return True

def cleanup_sites(token, url, dryrun=True):
    """Cleanup sites in Lab 1."""
    if dryrun:
        headers = {"x-auth-token": token, 'content-type': 'application/json'}
        try:
            response = requests.request("GET", url+"/dna/intent/api/v1/sites", headers=headers, verify=False)
            if response.status_code == 200:
                click.echo("Retrieving list of sites...")
                sites_dict = {}
                for site in response.json()["response"]:
                    if site.get("nameHierarchy"):
                        sites_dict[site["nameHierarchy"]] = [site["id"], site["type"]]


                floors = {k: v for k, v in sites_dict.items() if v[1] == 'floor'}
                buildings = {k: v for k, v in sites_dict.items() if v[1] == 'building'}
                areas = {k: v for k, v in sites_dict.items() if v[1] == 'area'}

                # Sort areas by the number of slashes in the key, in descending order
                sorted_areas = sorted(areas.items(), key=lambda item: item[0].count('/'), reverse=True)

                click.echo("Deleting floors...")
                for floor_name, floor in floors.items():
                    response = requests.request("DELETE", url+"/dna/intent/api/v2/floors/"+floor[0], headers=headers, verify=False)
                    if response.status_code == 202:
                        click.echo(f"Deleted floor: {floor_name}")
                    else:
                        click.echo(f"Failed to delete floor: {floor_name}. Status Code: {response.status_code}, Response: {response.text}")

                click.echo("Deleting buildings...")
                for building_name, building in buildings.items():
                    response = requests.request("DELETE", url+"/dna/intent/api/v2/buildings/"+building[0], headers=headers, verify=False)
                    if response.status_code == 202:
                        click.echo(f"Deleted building: {building_name}")
                    else:
                        click.echo(f"Failed to delete building: {building_name}. Status Code: {response.status_code}, Response: {response.text}")
            
                click.echo("Deleting areas...")
                for area in sorted_areas:
                    response = requests.request("DELETE", url+"/dna/intent/api/v1/areas/"+area[1][0], headers=headers, verify=False)
                    if response.status_code == 202:
                        click.echo(f"Deleted area: {area[0]}")
                    else:
                        click.echo(f"Failed to delete area: {area[0]}. Status Code: {response.status_code}, Response: {response.text}")
          
            else:
                click.echo(f"Failed to retrieve sites. Status Code: {response.status_code}, Response: {response.text}")
        except requests.exceptions.RequestException as e:
            click.echo(f"Failed to cleanup sites: {e}")

        click.echo("Sites cleaned up successfully.")
    else:
        click.echo("Sites cleaned up successfully. (dryrun)")
    return True

@click.group()
@click.option("--url", default="https://198.18.129.100", help="DNAC URL")
@click.option("--username", default="admin", help="DNAC Username")
@click.option("--password", default="C1sco12345", help="DNAC Password")
@click.pass_context
def cli(ctx, url, username, password):
    """A CLI tool for cleaning up DNAC configurations."""
    ctx.ensure_object(dict)
    ctx.obj["URL"] = url
    ctx.obj["USERNAME"] = username
    ctx.obj["PASSWORD"] = password

@cli.command()
@click.pass_context
def lab1(ctx):
    """Cleanup configuration for Lab 1."""
    token = authenticate(ctx.obj["URL"], ctx.obj["USERNAME"], ctx.obj["PASSWORD"])
    if token:
        cleanup_pools(token, ctx.obj["URL"])
        cleanup_sites(token, ctx.obj["URL"])
        click.echo("Cleaning up DNAC configuration for Lab 2...")
    else:
        click.echo("Unable to clean up Lab 2 due to authentication failure.")

@click.command()
@click.pass_context
def lab2(ctx):
    """Cleanup configuration for Lab 2."""
    # Add logic to cleanup Lab 2 configuration here
    click.echo("Cleaning up DNAC configuration for Lab 2...")

# Add commands to the main group
cli.add_command(lab1)
cli.add_command(lab2)

if __name__ == "__main__":
    cli()
