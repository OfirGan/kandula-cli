#!/usr/bin/env python3
from os import abort
import click
import boto3
from boto3 import client

def get_instance_value_by_key(instance, key: str):
    if key in instance:
        return instance[key]


def get_instance_state_reason(instance):
    state_name = instance["State"]["Name"]
    if state_name != "running" and state_name != "pending":
        return instance["StateReason"]["Message"]


def get_instance_mac_address(instance):
    if len(instance["NetworkInterfaces"]) > 0:
        return instance["NetworkInterfaces"][0]["MacAddress"]


def get_instance_network_interface_id(instance):
    if len(instance["NetworkInterfaces"]) > 0:
        return instance["NetworkInterfaces"][0]["NetworkInterfaceId"]


def get_instance_tags(instance):
    if "Tags" in instance:
        return instance["Tags"]
    return []


fields_translation_dict = {
    "Id": "InstanceId",
    "Type": "InstanceType",
    "ImageId": "ImageId",
    "LaunchTime": "LaunchTime",
    "SubnetId": "SubnetId",
    "VpcId": "VpcId",
    "PrivateDnsName": "PrivateDnsName",
    "PrivateIpAddress": "PrivateIpAddress",
    "PublicDnsName": "PublicDnsName",
    "PublicIpAddress": "PublicIpAddress",
    "RootDeviceName": "RootDeviceName",
    "RootDeviceType": "RootDeviceType",
    "SecurityGroups": "SecurityGroups",
}

def get_instances_dict_list(ec2_client):
        my_instances = ec2_client.describe_instances()
        instances_list = []
        instance_data_dict_list = []

        for instance in my_instances["Reservations"]:
            for instance_data in instance["Instances"]:
                instances_list.append(instance_data)

        for instance in instances_list:
            instance_data_dict = {}
            instance_data_dict["Cloud"] = "aws"
            instance_data_dict["Region"] = ec2_client.meta.region_name
            instance_data_dict["State"] = instance["State"]["Name"]

            for key, translated_key in fields_translation_dict.items():
                instance_data_dict[key] = get_instance_value_by_key(instance, translated_key)

            instance_data_dict["StateReason"] = get_instance_state_reason(instance)
            instance_data_dict["MacAddress"] = get_instance_mac_address(instance)
            instance_data_dict["NetworkInterfaceId"] = get_instance_network_interface_id(instance)
            instance_data_dict["Tags"] = get_instance_tags(instance)

            instance_data_dict_list.append(instance_data_dict)

        return instance_data_dict_list

def is_exist(ec2_client, instance_id):
    is_exist = False

    instance_data_dict_list = get_instances_dict_list(ec2_client)

    for instance_dict in instance_data_dict_list:
        if instance_dict['Id'] == instance_id:
            is_exist = True

    if not is_exist:
        click.echo("Instance ID not found")
        
    return is_exist

@click.group()
@click.option('--debug/--no-debug', is_flag=True, default=False)
@click.pass_context
def entry(context, debug):
    click.echo('Welcome To kancli' )
    context.obj['DEBUG'] = debug
    context.obj['ec2_client'] = boto3.client('ec2')

@entry.command()
@click.pass_context
def get_instances(context):
    instance_data_dict_list = get_instances_dict_list(context.obj['ec2_client'])
    for instance_dict in instance_data_dict_list:
        click.echo("---")
        click.echo(f"Instance ID: {instance_dict['Id']}")
        click.echo(f"Instance State: {instance_dict['State']}")

    click.echo("---")
    pass

@entry.command()
@click.pass_context
@click.option('-i', '--instance-id', 'instance_id',type = str, required = True, help = "Instance to start")
@click.confirmation_option(prompt=f'Are you sure you want to start the instance?')
def start_instance(context, instance_id):
    ec2_client = context.obj['ec2_client']
    if is_exist(ec2_client, instance_id):
        ec2_client.start_instances(InstanceIds=[instance_id])
    pass

@entry.command()
@click.pass_context
@click.option('-i', '--instance-id', 'instance_id',type = str, required = True, help = "Instance to stop")
@click.confirmation_option(prompt=f'Are you sure you want to stop the instance?')
def stop_instance(context, instance_id):
    ec2_client = context.obj['ec2_client']
    if is_exist(ec2_client, instance_id):
        ec2_client.stop_instances(InstanceIds=[instance_id])
    pass

@entry.command()
@click.pass_context
@click.option('-i', '--instance-id', 'instance_id',type = str, required = True, help = "Instance to terminate")
@click.confirmation_option(prompt=f'Are you sure you want to terminate the instance?')
def terminate_instance(context, instance_id):
    ec2_client = context.obj['ec2_client']
    if is_exist(ec2_client, instance_id):
        ec2_client.terminate_instances(InstanceIds=[instance_id])
    pass

if __name__ == '__main__':
    entry(obj={})
