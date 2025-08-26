# ARHF
This repository contains code for ARHF: Ambiguity Resolution with Human Feedback for Code Writing Tasks.

[ARHF: Ambiguity Resolution with Human Feedback for Code Writing Tasks](https://arxiv.org/abs/2508.14114)  
_Accepted at the International Conference on Computers in Education (ICCE 2025)._

## Overview
ARHF is a prototype system that helps programmers detect and resolve ambiguities in code-writing tasks.  
It integrates LLMs, automated testing, and limited human feedback to iteratively refine solutions.


## Abstract
Specifications for code writing tasks are usually expressed in natural language and may be ambiguous. Programmers must therefore develop the ability to recognize ambiguities in task specifications and resolve them by asking clarifying questions. We present and evaluate a prototype system, based on a novel technique (ARHF: Ambiguity Resolution with Human Feedback), that (1) suggests specific inputs on which a given task specification may be ambiguous, (2) seeks limited human feedback about the code's desired behavior on those inputs, and (3) uses this feedback to generate code that resolves these ambiguities. We evaluate the efficacy of our prototype, and we discuss the implications of such assistive systems on Computer Science education.

## Installation

To install the repository, take the following steps:

```
# Clone the repository
git clone https://github.com/Nandan-Aditey/ARHF.git

# Go into the directory
cd ARHF

# Install dependencies
pip install -r requirements.txt
```

Git clone will clone or copy the repository locally. The 'requirements.txt' file contains various dependendencies required to run this tool.

You can also create a virtual environment by:
```
# Create venv
python -m venv .arhf-venv

# Activate venv
# On Linux/macOS:
source .arhf-venv/bin/activate
# On Windows (PowerShell):
.arhf-venv\Scripts\Activate

```


## Usage

Run the tool via:
```
python main.py
```

- Generated programs are saved under: `Crosshair/Programs/`

- Create a `.env` file to store your API keys and Flask secrets (use `.env.example` as a template).

## Project

We create a system ARHF: Ambiguity Resolution with Human Feedback, which helps detect ambiguities present in natural language and ask clarifying questions to resolve these ambiguities.

The users inputs functions signature, docstring and doctest(s), and we generate a candidate implementation using a Code LLM. Along with this, we also generate a list of test inputs using a Code LLM, as well as using Crosshair (symbolic execution tool). The candidate implementation is run on these inputs to get a list of input-output pairs, which we refer to as doctests.

The doctests act as clarifying questions, users can either 'accept' the doctest, if the desired output on the input is the same as the generated output, or select 'reject' and specify the desired output on the input.

Using these corrected doctests, we ask the LLM to update the code to adhere to the doctests. A loop has been setup where we retry to get the LLM to generate the desired interpretation till the time it does or it hits an upper bound of number of retries (Number used in paper: 1).

> [!WARNING]  
> The "refute" button workflow (shown after the tool provides the user with the generated code) is still under development and is not part of the architecture described in the paper.

## Citation

If you use or reference this work in your research, please cite it as:

``` bibtex
 @inproceedings{nandankumarahrf,
  title={Ambiguity Resolution with Human Feedback for Code Writing Tasks},
  author={Nandan, Aditey and Kumar, Viraj},
  booktitle={Proceedings of the 33rd International Conference on Computers in Education (ICCE 2025)},
  publisher={Asia-Pacific Society for Computers in Education (APSCE)},
  year={2025},
  doi={10.48550/arXiv.2508.14114},
  archivePrefix={arXiv},
  eprint={2508.14114},
  primaryClass={cs.SE}
}
```


## License

This project is licensed under the [MIT License](./LICENSE) © 2025 Aditey Nandan.
