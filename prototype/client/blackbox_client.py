import argparse
import grpc
import time
import proto.blackbox_server_pb2 as server_pb2
import proto.blackbox_variable_pb2 as variable_pb2
import proto.blackbox_server_pb2_grpc as pb_grpc


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', help='path to binary')
    parser.add_argument('--l')
    parser.add_argument('--r')
    return parser.parse_args()


def generate_request(file_name, l, r):
    header = server_pb2.NewTaskRequest()
    variable = variable_pb2.BlackboxVariable()
    variable.name = 'main'
    variable.continious_variable.l = float(l)
    variable.continious_variable.r = float(r)
    variable.direct_input.SetInParent()
    header.metadata.task_variables.append(variable)
    yield header

    with open(file_name, 'rb') as f:
        data = f.read(4096)
        block = server_pb2.NewTaskRequest()
        block.body.chunk = data
        yield block


def main():
    args = parse_args()
    print(args)
    channel = grpc.insecure_channel('localhost:50051')
    stub = pb_grpc.BlackboxStub(channel)
    response = stub.NewTask(generate_request(args.binary, args.l, args.r))
    task_id = response.task_id
    print(response)
    while True:
        print('Trying querying')
        request = server_pb2.GetTaskResultRequest()
        request.task_id = task_id
        try:
            response = stub.GetTaskResult(request)
            print(response)
            break
        except grpc.RpcError as e:
            status_code = e.code()
            if status_code != grpc.StatusCode.UNAVAILABLE:
                raise e
        time.sleep(1)
    


if __name__ == '__main__':
    main()
