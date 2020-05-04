import grpc
import uuid
import os
import subprocess
from concurrent import futures

import prototype.server.config as config
import prototype.server.storage as storage
import prototype.server.proto.blackbox_server_pb2 as pb2
import prototype.server.proto.blackbox_server_pb2_grpc as pb2_grpc


def _launch_optimizer(task_id, metadata, task_path):
    p = subprocess.Popen(
        ['prototype/server/blackbox_optimizer', task_id, task_path],
        close_fds=True,
        stdin=subprocess.PIPE,
    )
    p.stdin.write(metadata.SerializeToString())
    p.stdin.flush()
    p.stdin.close()


class BlackboxServer(pb2_grpc.BlackboxServicer):
    def NewTask(self, request_iter, context):
        header = request_iter.next().metadata

        task_id = str(uuid.uuid4())
        file_path = os.path.join(config.BINARIES_FOLDER, task_id)
        with open(file_path, 'wb') as f:
            for block in request_iter:
                body = block.body
                f.write(body.chunk)
        st = os.stat(file_path)
        os.chmod(file_path, st.st_mode | 0o111)

        _launch_optimizer(task_id, header, file_path)
        
        response = pb2.NewTaskResponse()
        response.task_id = task_id
        return response

    def GetTaskResult(self, request, context):
        stor = storage.TaskStorageSqlite()
        try:
            result = stor.get_task_result(request.task_id)
            return result
        except KeyError:
            msg = 'No completed task found'
            context.set_details(msg)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return pb2.GetTaskResultResponse()


def main():
    storage.TaskStorageSqlite.init_database()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_BlackboxServicer_to_server(BlackboxServer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    main()
