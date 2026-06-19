import unittest


class SeedRolesPermissionsCommandTest(unittest.TestCase):
    def test_parser_requires_organization_and_accepts_actor_and_dry_run(self) -> None:
        from src.modules.admin.seed_roles_permissions import build_parser

        parser = build_parser()
        args = parser.parse_args(
            [
                "--organization-id",
                "11111111-1111-4111-8111-111111111111",
                "--actor-user-id",
                "22222222-2222-4222-8222-222222222222",
                "--dry-run",
            ]
        )

        self.assertEqual(
            "11111111-1111-4111-8111-111111111111",
            args.organization_id,
        )
        self.assertEqual(
            "22222222-2222-4222-8222-222222222222",
            args.actor_user_id,
        )
        self.assertTrue(args.dry_run)


if __name__ == "__main__":
    unittest.main()
