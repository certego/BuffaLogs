from django.core.management.base import BaseCommand, CommandError
from impossible_travel.constants import UserRiskScoreType
from impossible_travel.management.commands.base_command import TaskLoggingCommand
from impossible_travel.models import User

VALID_RISK_SCORES = list(UserRiskScoreType.values)


class Command(TaskLoggingCommand):
    help = "Reset or update user risk_score values."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--username",
            type=str,
            help="Specify username to update (optional)",
        )
        parser.add_argument(
            "--risk_score",
            type=str,
            default=UserRiskScoreType.NO_RISK.value,
            help=f"Specify risk score to set (default: '{UserRiskScoreType.NO_RISK.value}')",
        )

    def handle(self, *args, **options):
        username = options.get("username")
        risk_score = options.get("risk_score")

        # Validate risk_score
        if risk_score not in VALID_RISK_SCORES:
            raise CommandError(
                f"Invalid risk_score '{risk_score}'. Valid values are: {', '.join(VALID_RISK_SCORES)}"
            )

        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f"User '{username}' does not exist.")

            user.risk_score = risk_score
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated risk_score for user '{username}' to '{risk_score}'."
                )
            )
        else:
            count = User.objects.update(risk_score=risk_score)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated risk_score for {count} users to '{risk_score}'."
                )
            )
