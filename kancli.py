#!/usr/bin/env python3
import logging
import logging.handlers
import click
import boto3
from boto3 import client
from tabulate import tabulate

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

def get_exception_error(ex):
    return str(ex).split(':', 1)[-1].lstrip()

def init_logger(debug_enabled: bool):
    logging.getLogger('boto3').setLevel(logging.CRITICAL)
    logging.getLogger('botocore').setLevel(logging.CRITICAL)
    logging.getLogger('s3transfer').setLevel(logging.CRITICAL)
    logging.getLogger('urllib3').setLevel(logging.CRITICAL)
    
    logging.basicConfig(level=logging.DEBUG,handlers=[])
    logging_level = logging.DEBUG if debug_enabled else logging.ERROR

    # DEBUG \ ERROR Log To stdout
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging_level)
    stream_handler.setFormatter(logging.Formatter('%(message)s'))
    
    # DEBUG Log To File 
    file_handler = logging.handlers.TimedRotatingFileHandler(filename='kandula.log', when='midnight', backupCount=10)
    file_handler.setLevel(logging_level)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(filename)s [%(levelname)s]: %(message)s'))
    
    logger = logging.getLogger()
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger
    
@click.group()
@click.option('--debug/--no-debug', is_flag=True, default=False)
@click.pass_context
def entry(context, debug):
    click.secho('Welcome to kancli \n', fg="cyan", bold=True, underline=True)
    context.obj['ec2_client'] = boto3.client('ec2')
    context.obj['logger'] = init_logger(debug)

@entry.command()
@click.pass_context
def get_instances(context):
    context.obj['logger'].info("get_instances() - Started")
    try:
        headers_list = ["Id", "Region", "Type", "State", "PrivateIpAddress", "PublicIpAddress"]
        table_data = []
        instance_data_dict_list = get_instances_dict_list(context.obj['ec2_client'])
        for instance_dict in instance_data_dict_list:
            instance_row = []
            for header in headers_list:
                instance_row.append(instance_dict[header])
            table_data.append(instance_row)

        click.echo(tabulate(table_data, headers = headers_list))
        context.obj['logger'].info("get_instances() - Finished Successfully")
    except Exception as ex:
        context.obj['logger'].error(get_exception_error(ex))
        context.obj['logger'].info("get_instances() - Finished with Error")

@entry.command()
@click.pass_context
@click.option('-i', '--instance-id', 'instance_id',type = str, required = True, help = "Instance to start")
@click.confirmation_option(prompt='Are you sure you want to start the instance?')
def start_instance(context, instance_id):
    context.obj['logger'].info("start_instance() - Started")
    ec2_client = context.obj['ec2_client']
    try:
        ec2_client.start_instances(InstanceIds=[instance_id])
        context.obj['logger'].info(f"{instance_id} - Started")
        context.obj['logger'].info("start_instance() - Finished Successfully")
    except Exception as ex:
        context.obj['logger'].error(get_exception_error(ex))
        context.obj['logger'].info("start_instance() - Finished with Error")

@entry.command()
@click.pass_context
@click.option('-i', '--instance-id', 'instance_id',type = str, required = True, help = "Instance to stop")
@click.confirmation_option(prompt='Are you sure you want to stop the instance?')
def stop_instance(context, instance_id):
    context.obj['logger'].info("stop_instance() - Started")
    ec2_client = context.obj['ec2_client']
    try:
        ec2_client.stop_instances(InstanceIds=[instance_id])
        context.obj['logger'].info(f"{instance_id} - Stopped")
        context.obj['logger'].info("stop_instance() - Finished Successfully")
    except Exception as ex:
        context.obj['logger'].error(get_exception_error(ex))
        context.obj['logger'].info("stop_instance() - Finished with Error")

@entry.command()
@click.pass_context
@click.option('-i', '--instance-id', 'instance_id',type = str, required = True, help = "Instance to terminate")
@click.confirmation_option(prompt='Are you sure you want to terminate the instance?')
def terminate_instance(context, instance_id):
    context.obj['logger'].info("terminate_instance() - Started")
    ec2_client = context.obj['ec2_client']
    try:
        ec2_client.terminate_instances(InstanceIds=[instance_id])
        context.obj['logger'].info(f"{instance_id} - Terminated")
        context.obj['logger'].info("terminate_instance() - Finished Successfully")
    except Exception as ex:
        context.obj['logger'].error(get_exception_error(ex))
        context.obj['logger'].info("terminate_instance() - Finished with Error")

if __name__ == '__main__':
        entry(obj = {})
