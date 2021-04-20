from aws_cdk import core as cdk,\
    aws_lambda_python as python_lambda,\
    aws_events as events,\
    aws_events_targets as targets,\
    aws_logs as logs,\
    aws_cloudwatch as cloudwatch,\
    aws_cloudwatch_actions as cloudwatch_actions,\
    aws_sns as sns

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core


class VaccineCheckerStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        handler = python_lambda.PythonFunction(self, "checker",
            entry="checker_function",
            memory_size=256,
            timeout=cdk.Duration.minutes(5),
            log_retention=logs.RetentionDays.ONE_MONTH
        )

        availability_metric = cloudwatch.Metric(
            metric_name="appointments_available",
            namespace="VaccineChecker",
            period=cdk.Duration.minutes(5)
        )

        rule = events.Rule(self, "rule",
            schedule=events.Schedule.rate(availability_metric.period))

        rule.add_target(targets.LambdaFunction(handler))

        logs.MetricFilter(self, "filter",
            log_group=handler.log_group,
            filter_pattern=logs.FilterPattern.all_terms("available"),
            metric_name=availability_metric.metric_name,
            metric_namespace=availability_metric.namespace,
            default_value=0
        )

        alarm_topic = sns.Topic(self, "alarmTopic",
            topic_name="VaccineCheckerNotify")

        failure_alarm = cloudwatch.Alarm(self, "checkerFailureAlarm",
            metric=handler.metric_errors(),
            evaluation_periods=1,
            threshold=0,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            statistic="max",
            alarm_name="VaccineCheckerFailureAlarm",
            alarm_description="Vaccine checker function failure",
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        failure_alarm.add_alarm_action(cloudwatch_actions.SnsAction(alarm_topic))

        availability_alarm = cloudwatch.Alarm(self, "availabilityAlarm",
            metric=availability_metric,
            evaluation_periods=1,
            threshold=0,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            statistic="sum",
            alarm_name="VaccineAvailabilityAlarm",
            alarm_description="Vaccine appoints are available"
        )
        availability_alarm.add_alarm_action(cloudwatch_actions.SnsAction(alarm_topic))

        high_availability_alarm = cloudwatch.Alarm(self, "highAvailabilityAlarm",
            metric=availability_metric,
            evaluation_periods=1,
            threshold=10,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            statistic="sum",
            alarm_name="VaccineHighAvailabilityAlarm",
            alarm_description="A high number of vaccine appointments are available")
        high_availability_alarm.add_alarm_action(cloudwatch_actions.SnsAction(alarm_topic))
