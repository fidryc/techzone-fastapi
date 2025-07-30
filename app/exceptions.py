from fastapi import HTTPException, status

HttpExc401Unauth = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

def HttpExc401Unauth(detail) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

def HttpExc409Conflict(detail) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

        
