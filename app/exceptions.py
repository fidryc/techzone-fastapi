from fastapi import HTTPException, status

HttpExc401Unauth = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

def HttpExc401Unauth(detail) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

def HttpExc409Conflict(detail) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

def HttpExc403Forbidden(detail) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
        
def HttpExc422UnprocessableEntity(detail) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class DataBaseException(Exception): pass

class RefreshTokenBLServiceException(Exception): pass