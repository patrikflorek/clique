"""
This module provides a GUI tool for collecting answers from a human client
based on provided questions and respective options in a questionnaire.
"""

from textwrap import dedent

from typing import Dict, List, Type

from pydantic import BaseModel, Field

import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap import Style
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.constants import *

from crewai_tools import BaseTool

# Constants for window size and text wrap length
WINDOW_SIZE = (480, 640)
WRAP_LENGTH = WINDOW_SIZE[0] - 60


class Header(ttk.Frame):
    """
    A frame that displays the header of the questionnaire, including the title,
    author, and introduction.
    """

    def __init__(self, master, title, author, introduction, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.title = title
        self.author = author
        self.introduction = introduction

        self.create_widgets()

    def create_widgets(self) -> None:
        """Create and pack the widgets for the header."""
        ttk.Label(
            self,
            text=self.title,
            font=("Helvetica", 16, "bold"),
            justify=CENTER,
            wraplength=WRAP_LENGTH,
            bootstyle=PRIMARY,
        ).pack(pady=10)

        ttk.Label(
            self,
            text=self.author,
            font=("Helvetica", 12, "bold"),
            justify=CENTER,
            wraplength=WRAP_LENGTH,
            bootstyle=SECONDARY,
        ).pack(pady=5)

        ttk.Label(
            self,
            text=self.introduction,
            font=("Helvetica", 12),
            justify=LEFT,
            wraplength=WRAP_LENGTH,
            bootstyle=DEFAULT,
        ).pack(pady=10)


class OptionFrame(ttk.Frame):
    """
    A frame that displays an option for a question, including a check button
    and a label for the option text.
    """

    def __init__(self, master, option, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.option = option

        self.create_widgets()

    def create_widgets(self) -> None:
        """Create and pack the widgets for the option."""
        self.check_button = ttk.Checkbutton(self)
        self.check_button.pack(side=LEFT)

        ttk.Label(self, text=self.option, wraplength=WRAP_LENGTH, justify=LEFT).pack(
            side=LEFT
        )


class CommentFrame(ttk.Frame):
    """
    A frame that allows the client to add additional comments.
    """

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)

        self.create_widgets()

    def create_widgets(self) -> None:
        """Create and pack the widgets for the comment section."""
        ttk.Label(
            self,
            text="Any other comments?",
            font=("Helvetica", 12, "bold"),
            justify=LEFT,
            wraplength=WRAP_LENGTH,
            bootstyle=PRIMARY,
            anchor=W,
        ).pack(side=TOP, padx=10, pady=10, anchor=W)

        self.comment = tk.Text(self, height=4)
        self.comment.pack(fill=X, pady=10)


class QuestionFrame(ttk.Frame):
    """
    A frame that displays a question and its options.
    """

    def __init__(self, master, question_data, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.question_data = question_data

        self.create_widgets()

    def create_widgets(self) -> None:
        """Create and pack the widgets for the question and its options."""
        self.question_label = ttk.Label(
            self,
            text=self.question_data["question"],
            font=("Helvetica", 12, "bold"),
            justify=LEFT,
            wraplength=WRAP_LENGTH,
            bootstyle=PRIMARY,
            anchor=W,
        )
        self.question_label.pack(side=TOP, padx=10, pady=10, anchor=W)

        options = self.question_data.get("options", [])
        self.option_frames = []
        for option in options:
            option_frame = OptionFrame(self, option)
            option_frame.pack(fill=X, pady=5)
            self.option_frames.append(option_frame)

        self.custom_option = tk.Text(self, height=2)
        self.custom_option.pack(fill=X, pady=10)


class QuestionnaireFrame(ScrolledFrame):
    """
    A frame that contains the entire questionnaire, including the header,
    questions, and comment section.
    """

    def __init__(
        self,
        window,
        title,
        author,
        introduction,
        questions,
        on_client_response,
        **kwargs,
    ) -> None:
        super().__init__(master=window, autohide=YES, **kwargs)
        self.title = title
        self.author = author
        self.introduction = introduction
        self.questions = questions

        self.on_client_response = on_client_response

        self.create_widgets()

    def create_widgets(self) -> None:
        """Create and pack the widgets for the entire questionnaire."""
        Header(
            self,
            title=self.title,
            author=self.author,
            introduction=self.introduction,
        ).pack(anchor=CENTER)

        ttk.Separator(self, orient=HORIZONTAL).pack(fill=X, pady=20)

        questions_container = ttk.Frame(self)
        questions_container.pack(anchor=CENTER)

        self.question_frames = []
        for question_data in self.questions:
            question_frame = QuestionFrame(questions_container, question_data)
            question_frame.pack(fill=X, padx=10, pady=10)
            self.question_frames.append(question_frame)

        self.comment_frame = CommentFrame(questions_container)
        self.comment_frame.pack(fill=X, padx=10, pady=10)

        ttk.Separator(self, orient=HORIZONTAL).pack(fill=X, pady=20)

        ttk.Button(self, text="Submit", command=self.submit).pack(side=BOTTOM, pady=10)

    def submit(self) -> None:
        """Collect the client's responses and call the callback function."""
        client_response_lines = [f'Client answers to the questionnaire "{self.title}":']

        for question_frame in self.question_frames:
            question_label = question_frame.question_label.cget("text")
            client_response_lines.append(f"\n{question_label}")

            for option_frame in question_frame.option_frames:
                option = option_frame.option
                checked = option_frame.check_button.instate(["selected"])
                if checked:
                    client_response_lines.append(f"  * {option}")

            custom_option = question_frame.custom_option.get("1.0", "end-1c")
            if custom_option:
                client_response_lines.append(f"  + {custom_option}")

        comment = self.comment_frame.comment.get("1.0", "end-1c")
        if comment:
            client_response_lines.append(f"\nClient comments:\n{comment}")

        client_response = "\n".join(client_response_lines)
        self.on_client_response(client_response)


class Questionnaire:
    """
    A class that represents the entire questionnaire process, including
    displaying the GUI and collecting the client's responses.
    """

    def __init__(
        self,
        title: str,
        author: str,
        introduction: list,
        questions: List[Dict[str, List[str]]],
    ) -> None:
        self.title = title
        self.author = author
        self.introduction = introduction
        self.questions = questions

        self.client_response = None

    def on_client_response(self, response: str) -> None:
        """Callback function to handle the client's response."""
        self.client_response = response
        self.window.destroy()

    def get_client_response(self) -> str:
        """Display the questionnaire GUI and return the client's response."""
        self.window = ttk.Window(title="Client Questionnaire", size=WINDOW_SIZE)
        Style(theme="journal")

        qf = QuestionnaireFrame(
            self.window,
            self.title,
            self.author,
            self.introduction,
            self.questions,
            self.on_client_response,
        )
        qf.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.window.mainloop()

        return self.client_response


class QuestionSchema(BaseModel):
    """Schema for a single question in the questionnaire."""

    question: str = Field(..., description="Question to ask the client.")
    options: List[str] = Field(
        default_factory=list,
        description="List of options to choose to answer the question.",
    )


class QuestionnaireSchema(BaseModel):
    """Schema for the entire questionnaire."""

    title: str = "Title of the questionnaire."
    author: str = "Name or role of an agent who is the author of the questionnaire."
    introduction: str = (
        "Short introduction to the questionnaire and instructions for the client."
    )
    questions: List[QuestionSchema] = Field(
        ..., description="List of questions with their respective options."
    )


class ClientQuestionnaireTool(BaseTool):
    """
    A tool that uses a GUI to collect answers from a human client based on
    provided questions and respective options in a questionnaire.
    """

    name: str = "Client Questionnaire Tool"
    description: str = dedent(
        """
        This tools uses GUI to collects answers from a human client based 
        on provided questions and respective options in a questionnaire.
        """
    )
    args_schema: Type[BaseModel] = QuestionnaireSchema

    client_response: str = dedent(
        """
        Client answers to the questionnaire "{title}":

        {question_A}
            * {option_A1}
            * {option_A2}
              ...
            + {optional_client_custom_options_A}>

        {question_B}
            * {option_B1}
            * {option_B2}
                ...
            + {optional_client_custom_options}

        ...

        Client comments:
        {client_comments}
        """
    )

    def _run(self, **kwargs) -> str:
        """Run the tool to display the questionnaire and collect responses."""
        title = kwargs.get("title", "No title")
        author = kwargs.get("author", "No author")
        introduction = kwargs.get("introduction", "No introduction")
        questions = [question.dict() for question in kwargs.get("questions", [])]

        q = Questionnaire(title, author, introduction, questions)
        result = q.get_client_response()

        return result
