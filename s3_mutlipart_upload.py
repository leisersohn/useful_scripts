import boto3
import json
import multiprocessing

s3_client = boto3.client('s3')

#set hardcoded variables
bucket = '[bucket_name]'
file = 'example.mp4'
key = 'exampleTarget.mp4'

#define Create MultiPart
def start_upload():
    response = s3_client.create_multipart_upload(
        Bucket = bucket,
        Key = key
    )

    return response['UploadId']


#define Upload part
def add_part(proc_queue, body, bucket, key, part_number, upload_id):
    response = s3_client.upload_part(
        Body = body,
        Bucket = bucket,
        Key = key,
        PartNumber = part_number,
        UploadId = upload_id
    )

    print(f"Finished part: {part_number}, ETag: {response['ETag']}")
    proc_queue.put({'PartNumber': part_number, 'ETag': response['ETag']})
    return

#define End Upload
def end_upload(bucket, key, upload_id, finished_parts):
    response = s3_client.complete_multipart_upload(
        Bucket = bucket,
        Key = key,
        MultipartUpload={
            'Parts': finished_parts
        },
        UploadId = upload_id
    )

    return response

#actual script

#Open file in read mode
file_upload = open(file,'rb')

#Start process and get UploadID
upload_id = start_upload()

#set size for each part in MiB
chunk_size = 10 * 1024 * 1024
#read first chunck from input
chunk = file_upload.read(chunk_size)
part_num = 1

#Set queue variables to be used later for listing, starting and getting the status of the processes
proc_queue = multiprocessing.Queue()
part_procs = []
queue_returns = []

#Create list of processes based on file size and chunk size (each process is one part to upload)
while len(chunk) > 0:
    proc = multiprocessing.Process(target=add_part, args=(proc_queue, chunk, bucket, key, part_num, upload_id))
    part_procs.append(proc)
    part_num += 1
    chunk = file_upload.read(chunk_size)

#Start processes (start upload)
for p in part_procs:
    p.start()
    print('Started upload process for one part')

#Wait for parallel processes to finish
for p in part_procs:
    p.join()

#Retrieve processes from multiproces queue
for p in part_procs:
    queue_returns.append(proc_queue.get())

queue_returns = sorted(queue_returns, key = lambda i: i['PartNumber'])
#Finish MultiUpload process by providing list of all parts processed (uploaded)
response = end_upload(bucket, key, upload_id, queue_returns)
print(json.dumps(response, sort_keys=True, indent=4))
