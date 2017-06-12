from share.regulate.errors import RegulatorError


class BaseStep:
    def info(self, job, description, node_id=None):
        """Log information about a change made to the graph.
        """
        # TODO keep a list of logs, save them at the end?
        job.regulator_logs.create(description=description, node_id=node_id)

    def reject(self, job, description, node_id=None):
        """Indicate a regulated graph can be saved, but will not be merged into the SHARE dataset.
        """
        job.regulator_logs.create(description=description, node_id=node_id)
        # TODO don't merge suid with anything else

    def fail(self, job, description, node_id=None):
        """Indicate a severe problem with the data, halt regulation.
        """
        job.regulator_logs.create(description=description, rejected=True, node_id=node_id)
        raise RegulatorError('Regulation failed: {}'.format(description))


class BaseGraphStep(BaseStep):
    def regulate_graph(self, job, graph):
        raise NotImplementedError()


class BaseNodeStep(BaseStep):
    def regulate_node(self, job, node):
        raise NotImplementedError()


class BaseValidationStep(BaseStep):
    def validate_graph(self, job, graph):
        raise NotImplementedError()
