#### Blunt Assessment

**The current implementation does not and cannot achieve its stated goal.**

The core flaw lies in the generation strategy within `src/core/generator.py`. The script currently asks OpenAI to generate each PBR map (`diffuse`, `normal`, `roughness`, etc.) individually via a text prompt. A text-to-image model like DALL-E does not understand the technical requirements of a PBR workflow.

*   It will generate a **picture of a normal map** (a blue/purple image), not a technically correct normal map derived from surface details.
*   It will generate a **picture of a roughness map** (a grayscale image), not a map where pixel values accurately correspond to the microsurface properties of the base material.

This approach results in a set of disconnected, artistically-interpreted images that are functionally useless as a PBR material in Blender or any other 3D engine.

#### Current State vs. Desired State

| Aspect | Current Implementation (Flawed) | Desired Implementation (Correct) |
| :--- | :--- | :--- |
| **API Calls** | Multiple calls to OpenAI, one for each map type (e.g., "generate a normal map of bricks"). | **One primary API call** to generate a high-quality **Diffuse/Albedo** map. |
| **PBR Map Creation** | Assumes OpenAI can generate technically correct maps from text. | **Derives** other maps (Normal, Roughness, AO, Height) from the generated Diffuse map using image processing techniques. |
| **Tessellation** | The project name includes "Tessellating," but there is **no code to check, enforce, or correct seamless tiling**. It only *asks* the AI to make it seamless. | **Implements an image processing step** to analyze and ensure the Diffuse map is perfectly tileable *before* deriving other maps. |
| **Configuration Use**| The material properties in `config.json` (e.g., `roughness_range`) are **not used** in the generation process. | The material properties **drive the image processing algorithms** (e.g., `roughness_range` controls the contrast/levels of the derived roughness map). |
| **Code Implementation** | The Python `src/modules` and `src/utils/image_utils.py` are **empty skeletons** (`pass`). | These modules are **fully implemented** with image processing logic using libraries like `Pillow` and `OpenCV`. |

#### Architectural Disconnect

There is a major disconnect between the simple (but flawed) Python application and the sophisticated TypeScript architecture described in the documentation and test files.

*   **Python Side:** A linear script that makes a series of API calls.
*   **TypeScript Side:** Defines a complex, modular, stage-based pipeline (`Validate` -> `Generate Prompts` -> `Generate Textures` -> `Ensure Tessellation` -> `Export`).

The excellent README and `ARCHITECTURE.md` describe the aspirational TypeScript system, not the Python script that actually runs. **A decision must be made: either build out the Python application to match the documented architecture or pivot to a TypeScript/Node.js implementation.**

---

## TODO List for the Engineering Team

This roadmap is designed to pivot the project from its current state to a functional and valuable tool. It assumes the team will **continue with a Python implementation**, as it's better suited for the required image processing libraries.

### Phase 1: Foundational Rework & Strategy (Priority: Critical)

*   [ ] **1.1. (Decision) Solidify the Architecture:**
    *   **Task:** Formally decide to implement the core logic in Python. The existing TypeScript files should be treated as excellent reference/planning documents.
    *   **Goal:** Eliminate the architectural disconnect and provide a clear path forward.

*   [ ] **1.2. Correct the Core Generation Pipeline:**
    *   **Task:** Rework `src/core/generator.py` to follow the correct PBR derivation workflow:
        1.  Generate **only the diffuse (albedo) map** from OpenAI using an enhanced prompt.
        2.  Save the diffuse map.
        3.  Pass the diffuse map's image data to new, dedicated modules for generating the other maps.
    *   **Goal:** Fix the fundamental flaw in the generation process.

*   [ ] **1.3. Implement the PBR Derivation Modules (Skeletons to Substance):**
    *   **Task:** Flesh out the classes in `src/modules/`. Start with the most important maps.
        *   `normal.py`: Implement a function to generate a normal map from a grayscale version of the diffuse map. Libraries like `Pillow` or `numpy/scipy` can do this with Sobel filters.
        *   `roughness.py`: Implement a function that takes the diffuse map, converts it to grayscale, and uses the `roughness_range` from the config to adjust the levels/contrast to create a plausible roughness map.
        *   `height.py`: This can often be the same as the grayscale source used for the normal map.
    *   **Goal:** Create the core image processing logic that was missing.

*   [ ] **1.4. Update Documentation to Reflect Reality:**
    *   **Task:** Immediately update the `README.md` and `ARCHITECTURE.md` with a "Current Status" or "Roadmap" section to clarify that many features are planned, not implemented.
    *   **Goal:** Provide transparency and prevent confusion for new contributors or users.

---

### Phase 2: Implementing Key Features (Priority: High)

*   [ ] **2.1. Implement Tessellation/Seamless Tiling:**
    *   **Task:** Create a new module (`tessellation.py` or similar) that takes the generated diffuse map and makes it perfectly seamless.
    *   **Options:**
        1.  **Simple:** Image mirroring/flipping and blending at the seams.
        2.  **Advanced:** Use frequency-domain analysis (Fourier transform) or texture synthesis techniques.
    *   **Integration:** This step must happen **after** the diffuse map is generated but **before** any other PBR maps are derived from it.
    *   **Goal:** Deliver on the "Tessellating" promise of the project name.

*   [ ] **2.2. Integrate `config.json` Properties:**
    *   **Task:** Make the `material.properties` in the configuration file actually *do* something.
        *   `normal_strength`: Should be a parameter passed to the normal map generation function.
        *   `metallic_value`: If > 0, this should influence the roughness map and potentially create a solid-color metallic map.
    *   **Goal:** Make the tool configurable and powerful.

*   [ ] **2.3. Build out the Python Test Suite:**
    *   **Task:** The testing strategy is well-documented; now implement it in Python using `pytest`.
    *   Create `tests/` for Python: `tests/unit`, `tests/integration`.
    *   Write unit tests for the new image processing functions. Use sample images as fixtures.
    *   Mock the OpenAI API call to test the pipeline without incurring costs.
    *   **Goal:** Ensure the new, complex logic is reliable and bug-free.

---

### Phase 3: Blender Integration & User Experience (Priority: Medium)

*   [ ] **3.1. Create a Blender Add-on or Importer Script:**
    *   **Task:** Write a separate Python script (`blender_importer.py`) that can be run inside Blender.
    *   **Functionality:**
        1.  It should open a file dialog to select the folder of a generated texture set.
        2.  It should automatically create a new material in Blender.
        3.  It should create the full Principled BSDF node setup, connecting each texture map (diffuse, roughness, normal, etc.) to the correct input.
        4.  The "Normal Map" node should be automatically added for the normal texture.
    *   **Goal:** Fulfill the user story of having a "Blender compatible PBR material." This is a massive value-add.

*   [ ] **3.2. Implement Preview Generation:**
    *   **Task:** The config has a `create_preview` flag. Implement it. After generating the textures, use a library (e.g., with Blender as a background process, or a simpler 3D-renderer-in-python) to render a sphere or cube with the new material applied and save it as `preview.png`.
    *   **Goal:** Provide immediate visual feedback to the user.

---

### Phase 4: Refinement & Advanced Features (Priority: Low)

*   [ ] **4.1. Advanced Map Derivation:**
    *   **Task:** Improve the Ambient Occlusion (AO) map generation. Instead of just deriving from the diffuse, generate it from the derived height map for more accurate results.
    *   **Goal:** Increase the physical accuracy and quality of the generated materials.

*   [ ] **4.2. Improve CLI and User Feedback:**
    *   **Task:** Use a library like `tqdm` to show a progress bar during generation. Provide more verbose output on which map is currently being processed.
    *   **Goal:** Improve the user experience of the command-line tool.

*   [ ] **4.3. Explore Alternative Models/APIs:**
    *   **Task:** Abstract the API interface further to allow for plugging in other models like Stable Diffusion, which may offer more control or be more cost-effective.
    *   **Goal:** Make the tool more flexible and future-proof.