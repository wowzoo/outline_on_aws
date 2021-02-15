import boto3
import os


if __name__ == "__main__":
    domain_name = os.environ["DOMAIN_NAME"]
    bucket_name = f"outline-{'-'.join(domain_name.split('.'))}"

    print("Bucket Name :", bucket_name)

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    if bucket.creation_date is not None:
        print(f"\t{bucket.name}\t{bucket.creation_date}")
        bucket.objects.all().delete()
        bucket.delete()
    else:
        print("The bucket not exist")

