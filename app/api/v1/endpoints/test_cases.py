from fastapi import APIRouter, Depends, HTTPException
from app.db.session import get_db
from app.models.test_case import TestCase
from app.models.user import User
from app.schemas.test_case import (
    TestCase as TestCaseSchema,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseType,
)
from app.api.v1.endpoints.auth import fastapi_users
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter()

# Current user dependency
current_active_user = fastapi_users.current_user(active=True)

@router.post("/", response_model=TestCaseSchema)
async def create_test_case(
    *,
    db: AsyncSession = Depends(get_db),
    test_case_in: TestCaseCreate,
    current_user: User = Depends(current_active_user)
) -> TestCaseSchema:
    """
    Create a new test case.

    Args:
        test_case_in: The test case to create.
        current_user: The current user.

    Returns:
        The created test case.
    """
    # check if the test case type is valid
    valid_types = [t.lower() for t in TestCaseType]
    if test_case_in.type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid test case type")
    
    db_test_case = TestCase(
        name=test_case_in.name,
        type=test_case_in.type.lower(),
        input=test_case_in.input,
        expected_output=test_case_in.expected_output,
        context=test_case_in.context,
        retrieval_context=test_case_in.retrieval_context,
        additional_metadata=test_case_in.additional_metadata,
        is_global=test_case_in.is_global,
        user_id=str(current_user.id)
    )
    
    db.add(db_test_case)
    await db.commit()
    await db.refresh(db_test_case)
    
    return db_test_case

@router.get("/", response_model=list[TestCaseSchema])
async def read_test_cases(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user)
) -> list[TestCaseSchema]:
    """
    Get all test cases for the current user.

    Args:
        current_user: The current user.

    Returns:
        List of test cases.
    """
    query = select(TestCase).where(TestCase.user_id == str(current_user.id))
    result = await db.execute(query)
    test_cases = result.scalars().all()
    return test_cases

@router.get("/global", response_model=list[TestCaseSchema])
async def read_global_test_cases(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user)
) -> list[TestCaseSchema]:
    """
    Get all global test cases.

    Args:
        current_user: The current user.

    Returns:
        List of global test cases.
    """
    query = select(TestCase).where(TestCase.is_global == True)
    result = await db.execute(query)
    test_cases = result.scalars().all()
    return test_cases   

@router.get("/{test_case_id}", response_model=TestCaseSchema)
async def read_test_case(
    *,
    db: AsyncSession = Depends(get_db),
    test_case_id: str,
    current_user: User = Depends(current_active_user)
) -> TestCaseSchema:
    """
    Get a test case by ID.

    Args:
        test_case_id: The ID of the test case to get.
        current_user: The current user.

    Returns:
        The test case.
    """
    query = select(TestCase).where(
        TestCase.id == test_case_id,
        TestCase.user_id == str(current_user.id)
    )
    result = await db.execute(query)
    test_case = result.scalar_one_or_none()
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found or does not belong to current user")
    
    return test_case

@router.put("/{test_case_id}", response_model=TestCaseSchema)
async def update_test_case(
    *,
    db: AsyncSession = Depends(get_db),
    test_case_id: str,
    test_case_in: TestCaseUpdate,
    current_user: User = Depends(current_active_user)
) -> TestCaseSchema:
    """
    Update a test case.

    Args:
        test_case_id: The ID of the test case to update.
        test_case_in: The test case to update.
        current_user: The current user.

    Returns:
        The updated test case.
    """
    query = select(TestCase).where(
        TestCase.id == test_case_id,
        TestCase.user_id == str(current_user.id)
    )
    result = await db.execute(query)
    test_case = result.scalar_one_or_none()
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found or does not belong to current user")
    
    # Update fields
    update_data = test_case_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(test_case, field, value)
    
    await db.commit()
    await db.refresh(test_case)
    
    return test_case

@router.delete("/{test_case_id}", response_model=TestCaseSchema)
async def delete_test_case(
    *,
    db: AsyncSession = Depends(get_db),
    test_case_id: str,
    current_user: User = Depends(current_active_user)
) -> TestCaseSchema:
    """
    Delete a test case.

    Args:
        test_case_id: The ID of the test case to delete.
        current_user: The current user.

    Returns:
        The deleted test case.
    """
    query = select(TestCase).where(
        TestCase.id == test_case_id,
        TestCase.user_id == str(current_user.id)
    )
    result = await db.execute(query)
    test_case = result.scalar_one_or_none()
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found or does not belong to current user")
    
    await db.delete(test_case)
    await db.commit()
    
    return test_case 

@router.get("/type/{test_case_type}", response_model=list[TestCaseSchema])
async def read_test_cases_by_type(
    *,
    db: AsyncSession = Depends(get_db),
    test_case_type: str,
    current_user: User = Depends(current_active_user)
) -> list[TestCaseSchema]:
    """
    Get test cases by type.

    Args:
        test_case_type: The type of the test case to get.
        current_user: The current user.

    Returns:
        List of test cases.
    """
    # Convert to uppercase to match database enum values
    normalized_type = test_case_type.lower()
    
    # check if the test case type is valid
    valid_types = [t.lower() for t in TestCaseType]
    if normalized_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid test case type")
    
    query = select(TestCase).where(TestCase.type == normalized_type, TestCase.user_id == str(current_user.id))
    result = await db.execute(query)    

    test_cases = result.scalars().all()
    return test_cases