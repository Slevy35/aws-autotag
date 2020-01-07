import json
import boto3

def handler(event, context):

    result = None
    eventDetails = json.loads(json.dumps(event))["detail"]
    print(eventDetails)
    tags = [
        {'Key': 'Owner', 'Value': eventDetails["userIdentity"]["principalId"]},
        {'Key': 'OwnerARN', 'Value': eventDetails["userIdentity"]["arn"]},
        {'Key': 'Region', 'Value': eventDetails["awsRegion"]}
        ]
        
    # tag s3 buckets
    if (eventDetails["eventSource"] == 's3.amazonaws.com' and
        eventDetails["eventName"] == 'CreateBucket'):
        
        # Run tag_s3 function
        result = tag_s3(eventDetails["requestParameters"]["bucketName"], tags)
    # tag ec2 instances
    elif eventDetails["eventSource"] == "ec2.amazonaws.com":
        
        # Run tag_ec2 function
        result = tag_ec2(eventDetails["eventName"], eventDetails["responseElements"],tags)
    # tag CreateTrail trails
    elif (eventDetails["eventSource"] == "cloudtrail.amazonaws.com" and
        eventDetails["eventName"] == 'CreateTrail'):
        print("cloudtrail")
        # Run tag_trail function
        result = tag_trail(eventDetails["responseElements"],tags)
    # tag iam Roles and Policies
    elif eventDetails["eventSource"] == "iam.amazonaws.com":
        print("iam")
        # Run tag_iam function
        result = tag_iam(eventDetails["eventName"],eventDetails["responseElements"],tags)
    
    # print output
    print(result)

# Tag All EC2 Resources
def tag_ec2(eventName, responseElements, tags):
    ec2 = boto3.resource('ec2')
    
    ids = []

    if eventName == "RunInstances":
        #loop through instances"
        for item in responseElements["instancesSet"]["items"]:
            ids.append(item['instanceId'])
        base = ec2.instances.filter(InstanceIds=ids)
        #loop through connected resources"
        for instance in base:
            for vol in instance.volumes.all():
                ids.append(vol.id)
            for eni in instance.network_interfaces:
                ids.append(eni.id)
    elif eventName == 'CreateVolume':
        ids.append(responseElements['volumeId'])
    elif eventName == 'CreateImage':
        ids.append(responseElements['imageId'])
    elif eventName == 'CreateSnapshot':
        ids.append(responseElements['snapshotId'])
    elif eventName == 'CreateInternetGateway':
        ids.append(responseElements['internetGateway']['internetGatewayId'])
    elif eventName == 'CreateSecurityGroup':
        ids.append(responseElements['groupId'])
    elif eventName == 'CreateNetworkAcl':
        ids.append(responseElements['networkAcl']['networkAclId'])
    elif eventName == 'CreateVpc':
        ids.append(responseElements['vpc']['vpcId'])
    if ids:
        return ec2.create_tags(
                    Resources=ids,
                    Tags=tags
                )
    return "No IDs"

# Tag S3 Bucket
def tag_s3(bucketName, tags):
    s3 = boto3.client('s3')

    return s3.put_bucket_tagging(
        Bucket=bucketName,
        Tagging={
            'TagSet': tags
            }
    )

# Tag CloudTrail trail
def tag_trail(responseElements, tags):
    cloudtrail = boto3.client('cloudtrail')

    print(responseElements)
    return cloudtrail.add_tags(
        ResourceId = responseElements['trailid'],
        TagsList = tags
    )

# Tag IAM Roles and Policies
def tag_iam(eventName, responseElements, tags):
    iam = boto3.client('iam')
    
    print(responseElements)
    if eventName == 'CreateRole':
        print("CreateRole")
        
        return iam.tag_role(
            RoleName = responseElements['role']['roleName'],
            Tags = tags
        )