"""
This module contains the main logic of the interpreter.

IPP: You must definitely modify this file. Bend it to your will.

Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
Author: Andrej Bližnák <xblizna00@fit.vut.cz>
"""

import logging
from pathlib import Path
from typing import TextIO

from lxml import etree
from lxml.etree import ParseError
from pydantic import ValidationError

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.input_model import Program

logger = logging.getLogger(__name__)


class Interpreter:
    """
    The main interpreter class, responsible for loading the source file and executing the program.
    """

    def __init__(self) -> None:
        self.current_program: Program | None = None

    def load_program(self, source_file_path: Path) -> None:
        """
        Reads the source SOL-XML file and stores it as the target program for this interpreter.
        If any program was previously loaded, it is replaced by the new one.

        IPP: If you wish to run static checks on the program before execution, this is a good place
             to call them from.
        """
        logger.info("Opening source file: %s", source_file_path)
        try:
            xml_tree = etree.parse(source_file_path)
        except ParseError as e:
            raise InterpreterError(
                error_code=ErrorCode.INT_XML, message="Error parsing input XML"
            ) from e
        try:
            self.current_program = Program.from_xml_tree(xml_tree.getroot())  # type: ignore
        except ValidationError as e:
            raise InterpreterError(
                error_code=ErrorCode.INT_STRUCTURE, message="Invalid SOL-XML structure"
            ) from e

    def static_analyse(self):
        found_main = False
        found_run = False

        ## Opakujuce sa meno triedy
        if len(self.current_program.classes.name) != len(set(self.current_program.classes.name)):
            return 35
        for cls in self.current_program.classes:
            ## Dedenie samej zo seba
            if cls.parent == cls.name:
                return 35
            ## Najdenie "Mainu"
            if cls.name == "Main":
                found_main = True
                ## Hladanie "run"
                for main_mds in cls.methods:
                    if main_mds.selector == "run":
                        found_run = True
                        #### TODO: popnut teraz tu metodu zo zoznamu metod aby nebola dupli
                        ####       alebo iba pridat else pri for pre metody?
            for mds in cls.methods:
                self.check_block(self, mds.block)

        if not found_main or not found_run:
            return 31

    def check_block(self, block):
        if block.arity == len(block.parameters):
            if len(block.parameters) == len(set(block.parameters)):
                for assign in block.assigns:
                    self.check_expression(self, assign.expr)

    def check_expression(self, expression):
        if expression.block:
            self.check_block(self, expression.block)
        elif expression.send:
            ...

    def execute(self, input_io: TextIO) -> None:
        """
        Executes the currently loaded program, using the provided input stream as standard input.

        """
        logger.info("Executing program")
