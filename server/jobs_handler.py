import proto.jobs_handler_pb2 as pb2
import proto.jobs_handler_pb2_grpc as pb2_grpc
import server.storage as storage

import grpc
import uuid


def add_jobs_handler_to_server(server):
    pb2_grpc.add_JobsHandlerServicer_to_server(JobsHandlerServer(), server)


class JobsHandlerServer(pb2_grpc.JobsHandlerServicer):
    def __init__(self):
        super(JobsHandlerServer, self).__init__()
        self.storage_instance = storage.ServerStorage()
    
    def Heartbeat(self, request, context):
        self.storage_instance.update_client_heartbeat_time(request.client_id)
        response = pb2.HeartbeatResponse()
        response.active_workers = self.storage_instance.get_count_of_active_clients()
        return response

    def GetJob(self, request, context):
        job = self.storage_instance.get_job(request.client_id)
        if job is None:
            context.abort(
                grpc.StatusCode.UNAVAILABLE,
                'No job allocated'
            )
        response = pb2.GetJobResponse()
        response.job.CopyFrom(job)
        return response

    def NewJob(self, request, context):
        request.job.job_id = str(uuid.uuid4())
        self.storage_instance.add_job(request.job)
        response = pb2.NewJobResponse()
        response.job_id = request.job.job_id
        return response

    def GetJobResult(self, request, context):
        response = pb2.GetJobResultResponse()
        completed_job = self.storage_instance.get_completed_job(request.job_id)
        if completed_job is None:
            context.abort(
                grpc.StatusCode.UNAVAILABLE,
                'Job is not completed'
            )
        response.completed_job.CopyFrom(completed_job)
        return response

    def CompleteJob(self, request, context):
        self.storage_instance.complete_job(request.completed_job)
        return pb2.CompleteJobResponse()

    def GetJobData(self, request, context):
        for block in self.storage_instance.get_job_file_data(request.job_id):
            response = pb2.GetJobDataResponseChunk()
            response.chunk = block
            yield response
