"""
This module contains the main logic of the interpreter.

IPP: You must definitely modify this file. Bend it to your will.

Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
Author: Andrej Bližnák <xblizna00@fit.vut.cz>
"""

# ===========================================================
# Mine imports
# ===========================================================
from interpreter.dispatcher import Dispatcher
from interpreter.sol_objects import SolObject        
from interpreter.environment import Environment

# ===========================================================
# Default imports
# ===========================================================
import logging
from pathlib import Path
from typing import TextIO

from lxml import etree
from lxml.etree import ParseError
from pydantic import ValidationError

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.input_model import Program
from interpreter.static_analyzer import StaticAnalyzer

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

        #
        analyzer = StaticAnalyzer(self.current_program)
        analyzer.run()

    def execute(self, input_io: TextIO) -> None:
        """
        Executes the currently loaded program, using the provided input stream as standard input.

        """
        logger.info("Executing program")

        if self.current_program is None:
            return
        
        try:
            dispatcher = Dispatcher(self.current_program)

            main_instance = SolObject("Main")

            dispatcher.send_message(main_instance, "run", [], Environment())
        
        except InterpreterError as e:
            print(f"Runtime Error: {e}")
        except Exception as e:
            print(f"Internal Error: {e}")
