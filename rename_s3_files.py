import sys
import boto3

bucket_name = sys.argv[1]
bucket_prefix = sys.argv[2]
search_replace = sys.argv[3]
search_replace_2 = sys.argv[4]

s3 = boto3.client('s3')

if bucket_name and bucket_prefix:
    s3_objects = s3.list_objects(Bucket=bucket_name,Prefix=bucket_prefix)

    for file_list in s3_objects['Contents']:
        original_filename = file_list['Key']
        if search_replace:
            search_replace_list = search_replace.split('=')
        if search_replace_2:
            search_replace_list +=  search_replace_2.split('=')
        if len(search_replace_list) == int(4):
            new_filename = original_filename.replace(search_replace_list[0],search_replace_list[1])
            new_filename = new_filename.replace(search_replace_list[2],search_replace_list[3])
            if original_filename != new_filename:
                print("Copying {0} to {1}".format(original_filename,new_filename))
                copy_source = "{0}/{1}".format(bucket_name,original_filename)
                copy_action = s3.copy_object(Bucket=bucket_name,CopySource=copy_source,Key=new_filename)
                if copy_action['ResponseMetadata']['HTTPStatusCode'] == int(200):
                    print("Deleting original file {0}".format(original_filename))
                    s3.delete_object(Bucket=bucket_name,Key=original_filename)
                else:
                    print("Error in copying")                    
                    print(copy_action['ResponseMetaData']['HTTPStatusCode'])
            else:
                print("No changes for {0}".format(original_filename))            
        else:
            print("No search and replace input. Nothing to do!")
            
                
