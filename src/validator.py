from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TimelineMilestone(BaseModel):
    """Represents a specific milestone or phase in the project timeline."""
    milestone: str = Field(description="Name or title of the project milestone or phase")
    description: str = Field(default="Not specified in the source document", description="Details of deliverables for this milestone")
    start_date: Optional[str] = Field(default="Not specified in the source document", description="Estimated start date or offset")
    end_date: Optional[str] = Field(default="Not specified in the source document", description="Estimated completion date or offset")
    duration: Optional[str] = Field(default="Not specified in the source document", description="Duration (e.g., '2 weeks', '3 months')")
    source_page: Optional[str] = Field(default="Not specified in the source document", description="Source document page citation")


class MethodologyStep(BaseModel):
    """Represents an ordered step or phase within the project methodology."""
    step_number: int = Field(description="Sequential execution order")
    title: str = Field(description="Name of the methodology step, phase or approach")
    description: str = Field(description="Detailed explanation of activities, tools, or QA criteria")
    source_page: Optional[str] = Field(default="Not specified in the source document", description="Source document page citation")


class ProjectDocument(BaseModel):
    """
    Standardized, validated schema for project documentation.
    Strictly grounded in source text. No hallucinated information is permitted.
    """
    project_title: str = Field(
        description="The formal title of the project or proposal. Must not be empty."
    )
    scope_of_work: str = Field(
        description="Comprehensive summary of in-scope requirements, boundaries, and primary deliverables."
    )
    objectives: List[str] = Field(
        default_factory=list,
        description="List of primary and secondary project objectives."
    )
    methodology: List[MethodologyStep] = Field(
        default_factory=list,
        description="Ordered list of execution steps, technical approaches, frameworks, and QA procedures."
    )
    project_timeline: List[TimelineMilestone] = Field(
        default_factory=list,
        description="Structured timeline containing milestones, deliverables, dates, and durations."
    )
    source_references: List[str] = Field(
        default_factory=list,
        description="Verbatim page citations or excerpt references from the source PDF."
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Critical project dimensions not provided in the source PDF."
    )
    conflicting_information: List[str] = Field(
        default_factory=list,
        description="Contradictory statements or ambiguous specs identified in the document."
    )

    @field_validator("project_title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        cleaned = v.strip() if v else ""
        if not cleaned:
            return "Project Documentation (Title Not Specified in Source Document)"
        return cleaned

    @field_validator("objectives")
    @classmethod
    def validate_objectives_list(cls, v: List[str]) -> List[str]:
        if not v:
            return ["Not specified in the source document"]
        return [item.strip() for item in v if item and item.strip()]

    @field_validator("methodology")
    @classmethod
    def validate_methodology_list(cls, v: List[MethodologyStep]) -> List[MethodologyStep]:
        if not v:
            return [
                MethodologyStep(
                    step_number=1,
                    title="General Execution",
                    description="Methodology was not specified in the source document.",
                    source_page="Not specified in the source document"
                )
            ]
        # Ensure sequential numbering
        for idx, step in enumerate(v, start=1):
            step.step_number = idx
        return v

    @field_validator("project_timeline")
    @classmethod
    def validate_timeline_list(cls, v: List[TimelineMilestone]) -> List[TimelineMilestone]:
        if not v:
            return [
                TimelineMilestone(
                    milestone="Execution Phase",
                    description="Timeline schedule was not specified in the source document.",
                    start_date="Not specified in the source document",
                    end_date="Not specified in the source document",
                    duration="Not specified in the source document",
                    source_page="Not specified in the source document"
                )
            ]
        return v


def validate_project_data(data: dict) -> ProjectDocument:
    """
    Validates a raw dictionary against the ProjectDocument Pydantic schema.
    Sanitizes missing or malformed fields safely.
    """
    if not isinstance(data, dict):
        raise ValueError("Extraction payload must be a JSON object dictionary.")

    # Apply defaults if fields are entirely missing
    data.setdefault("project_title", "Project Documentation (Title Not Specified in Source Document)")
    data.setdefault("scope_of_work", "Not specified in the source document")
    data.setdefault("objectives", ["Not specified in the source document"])
    data.setdefault("methodology", [])
    data.setdefault("project_timeline", [])
    data.setdefault("source_references", [])
    data.setdefault("missing_information", [])
    data.setdefault("conflicting_information", [])

    return ProjectDocument.model_validate(data)
