class PoolEmptyException(Exception):
    def __str__(self) -> str:
        """
            Proxypool is used out
            :return: str
        """
        return repr('no proxy in pool')
