# SPDX-License-Identifier: Apache-2.0
"""Bootstrap package — stdlib-only helpers for installer and diagnostics.

Everything in this package MUST be importable without non-stdlib dependencies
(no PyYAML, no FastAPI, etc.). The bootstrap layer runs before ``uv sync``
has installed project dependencies, so any eager import of a third-party
package would crash the installer before it can report missing prerequisites.
"""
