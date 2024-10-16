from github import Auth, Github

private_key = """
OMITTED
"""


def test() -> str:
    print("Testing github")
    auth = Auth.AppAuth(app_id=0, private_key=private_key).get_installation_auth(
        installation_id=0
    )
    g = Github(auth=auth)

    print("Connected to Github")
    names = ""
    for repo in g.get_organization("OMITTED").get_repos():
        names += repo.name

    g.close()
    return names
