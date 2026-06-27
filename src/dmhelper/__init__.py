"""DM Helper package.

Tracing is disabled at import as a SAFE DEFAULT, so merely importing the
package (e.g. in tests) never uploads anything. The app turns tracing on
explicitly at startup via `dmhelper.observability.configure_tracing()`,
which only enables it when an OPENAI_API_KEY is present. Model calls always
route to Claude via LiteLLM regardless — the OpenAI key is used solely to
export traces to your OpenAI dashboard.
"""

from agents import set_tracing_disabled

set_tracing_disabled(True)

__all__ = ["set_tracing_disabled"]
