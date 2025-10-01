"""
Operational Transformation (OT) for Real-Time Collaborative Editing.

This module implements operational transformation algorithms to handle
concurrent edits in collaborative editing sessions without data loss.

Based on the principles from:
- Google's Wave OT algorithms
- Operational Transformation theory by Ellis and Gibbs
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum


class OperationType(str, Enum):
    """Types of operations supported."""

    INSERT = "insert"
    DELETE = "delete"
    RETAIN = "retain"


class Operation:
    """
    Represents a single operation in the document.

    Operations can be:
    - INSERT: Insert text at a position
    - DELETE: Delete text from start to end
    - RETAIN: Keep text unchanged (for composition)
    """

    def __init__(
        self,
        op_type: OperationType,
        position: Optional[int] = None,
        text: Optional[str] = None,
        length: Optional[int] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ):
        self.type = op_type
        self.position = position
        self.text = text
        self.length = length
        self.start = start
        self.end = end

    def to_dict(self) -> Dict[str, Any]:
        """Convert operation to dictionary format."""
        result: Dict[str, Any] = {"type": self.type.value}
        if self.position is not None:
            result["position"] = self.position
        if self.text is not None:
            result["text"] = self.text
        if self.length is not None:
            result["length"] = self.length
        if self.start is not None:
            result["start"] = self.start
        if self.end is not None:
            result["end"] = self.end
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Operation":
        """Create operation from dictionary."""
        return cls(
            op_type=OperationType(data["type"]),
            position=data.get("position"),
            text=data.get("text"),
            length=data.get("length"),
            start=data.get("start"),
            end=data.get("end"),
        )

    def __repr__(self) -> str:
        if self.type == OperationType.INSERT:
            return f"Insert('{self.text}' at {self.position})"
        elif self.type == OperationType.DELETE:
            return f"Delete({self.start}-{self.end})"
        else:
            return f"Retain({self.length})"


def apply_operation(document: str, operation: Operation) -> str:
    """
    Apply an operation to a document.

    Args:
        document: Current document text
        operation: Operation to apply

    Returns:
        Modified document text
    """
    if operation.type == OperationType.INSERT:
        position = operation.position or 0
        text = operation.text or ""
        return document[:position] + text + document[position:]

    elif operation.type == OperationType.DELETE:
        start = operation.start or 0
        end = operation.end or start + 1
        return document[:start] + document[end:]

    return document


def transform_operations(
    op1: Operation, op2: Operation, side: str = "left"
) -> Tuple[Operation, Operation]:
    """
    Transform two concurrent operations against each other.

    This is the core of Operational Transformation. When two operations
    are performed concurrently, we need to transform them so they can
    be applied in any order and produce the same result.

    Args:
        op1: First operation
        op2: Second operation
        side: Which operation has priority ("left" or "right")

    Returns:
        Tuple of transformed operations (op1', op2')
    """
    # INSERT vs INSERT
    if op1.type == OperationType.INSERT and op2.type == OperationType.INSERT:
        pos1 = op1.position or 0
        pos2 = op2.position or 0

        if pos1 < pos2 or (pos1 == pos2 and side == "left"):
            # op1 happens before op2
            op2_prime = Operation(
                OperationType.INSERT,
                position=pos2 + len(op1.text or ""),
                text=op2.text,
            )
            return op1, op2_prime
        else:
            # op2 happens before op1
            op1_prime = Operation(
                OperationType.INSERT,
                position=pos1 + len(op2.text or ""),
                text=op1.text,
            )
            return op1_prime, op2

    # INSERT vs DELETE
    elif op1.type == OperationType.INSERT and op2.type == OperationType.DELETE:
        pos1 = op1.position or 0
        start2 = op2.start or 0
        end2 = op2.end or start2 + 1

        if pos1 <= start2:
            # Insert happens before delete range
            op2_prime = Operation(
                OperationType.DELETE,
                start=start2 + len(op1.text or ""),
                end=end2 + len(op1.text or ""),
            )
            return op1, op2_prime
        elif pos1 >= end2:
            # Insert happens after delete range
            op1_prime = Operation(
                OperationType.INSERT,
                position=pos1 - (end2 - start2),
                text=op1.text,
            )
            return op1_prime, op2
        else:
            # Insert happens within delete range
            # Keep insert at boundary of delete
            op2_prime = Operation(
                OperationType.DELETE,
                start=start2,
                end=end2 + len(op1.text or ""),
            )
            return op1, op2_prime

    # DELETE vs INSERT
    elif op1.type == OperationType.DELETE and op2.type == OperationType.INSERT:
        # Symmetric case - swap and reverse
        op2_prime, op1_prime = transform_operations(
            op2, op1, "right" if side == "left" else "left"
        )
        return op1_prime, op2_prime

    # DELETE vs DELETE
    elif op1.type == OperationType.DELETE and op2.type == OperationType.DELETE:
        start1 = op1.start or 0
        end1 = op1.end or start1 + 1
        start2 = op2.start or 0
        end2 = op2.end or start2 + 1

        if end1 <= start2:
            # Delete ranges don't overlap, op1 is before op2
            op2_prime = Operation(
                OperationType.DELETE,
                start=start2 - (end1 - start1),
                end=end2 - (end1 - start1),
            )
            return op1, op2_prime
        elif end2 <= start1:
            # Delete ranges don't overlap, op2 is before op1
            op1_prime = Operation(
                OperationType.DELETE,
                start=start1 - (end2 - start2),
                end=end1 - (end2 - start2),
            )
            return op1_prime, op2
        else:
            # Delete ranges overlap
            # Calculate the non-overlapping parts
            new_start1 = min(start1, start2)
            new_end1 = min(end1, start2) if start1 < start2 else new_start1

            new_start2 = min(start2, start1)
            new_end2 = min(end2, start1) if start2 < start1 else new_start2

            if new_start1 == new_end1:
                # op1 is completely covered by op2
                op1_prime = Operation(
                    OperationType.DELETE,
                    start=new_start1,
                    end=new_start1,
                )
            else:
                op1_prime = Operation(
                    OperationType.DELETE,
                    start=new_start1,
                    end=new_end1,
                )

            if new_start2 == new_end2:
                # op2 is completely covered by op1
                op2_prime = Operation(
                    OperationType.DELETE,
                    start=new_start2,
                    end=new_start2,
                )
            else:
                op2_prime = Operation(
                    OperationType.DELETE,
                    start=new_start2,
                    end=new_end2,
                )

            return op1_prime, op2_prime

    # Default: return unchanged
    return op1, op2


def compose_operations(op1: Operation, op2: Operation) -> Optional[Operation]:
    """
    Compose two sequential operations into a single operation.

    This is used to optimize operation history by combining
    consecutive operations when possible.

    Args:
        op1: First operation
        op2: Second operation (applied after op1)

    Returns:
        Composed operation, or None if operations cannot be composed
    """
    # INSERT + INSERT at same position
    if (
        op1.type == OperationType.INSERT
        and op2.type == OperationType.INSERT
        and op1.position == op2.position
    ):
        return Operation(
            OperationType.INSERT,
            position=op1.position,
            text=(op1.text or "") + (op2.text or ""),
        )

    # INSERT + DELETE that deletes the inserted text
    if (
        op1.type == OperationType.INSERT
        and op2.type == OperationType.DELETE
        and op1.position is not None
        and op2.start == op1.position
        and op2.end == op1.position + len(op1.text or "")
    ):
        # Operations cancel out
        return None

    # Cannot compose
    return None


def transform_against_history(
    operation: Operation, history: List[Operation]
) -> Operation:
    """
    Transform an operation against a history of operations.

    This is used when a client's operation needs to be applied
    to a document that has been modified by other operations.

    Args:
        operation: Operation to transform
        history: List of operations that have been applied

    Returns:
        Transformed operation
    """
    transformed = operation

    for hist_op in history:
        transformed, _ = transform_operations(hist_op, transformed, "left")

    return transformed


def validate_operation(operation: Operation, document_length: int) -> bool:
    """
    Validate that an operation is valid for a document.

    Args:
        operation: Operation to validate
        document_length: Current length of the document

    Returns:
        True if operation is valid, False otherwise
    """
    if operation.type == OperationType.INSERT:
        position = operation.position or 0
        return 0 <= position <= document_length

    elif operation.type == OperationType.DELETE:
        start = operation.start or 0
        end = operation.end or start + 1
        return (
            0 <= start <= document_length
            and 0 <= end <= document_length
            and start <= end
        )

    return True


def create_insert_operation(position: int, text: str) -> Operation:
    """Helper to create an insert operation."""
    return Operation(OperationType.INSERT, position=position, text=text)


def create_delete_operation(start: int, end: int) -> Operation:
    """Helper to create a delete operation."""
    return Operation(OperationType.DELETE, start=start, end=end)
