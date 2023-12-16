from wiki import current_page_info


def lambda_handler(event: dict, context: object):  # type: ignore
    """Sample Lambda function which mocks the operation of selling a random number
    of shares for a stock.

    For demonstration purposes, this Lambda function does not actually perform any
    actual transactions. It simply returns a mocked result.

    Parameters
    ----------
    event: dict, required
        Input event to the Lambda function

    context: object, required
        Lambda Context runtime methods and attributes

    Returns
    ------
        dict: Object containing details of the stock selling transaction
    """
    title: str | None = event.get("title")  # type: ignore
    # url: str | None = event.get("url")

    info = current_page_info(title)  # type: ignore
    print(info)

    return {"has_new_revisions": False}
