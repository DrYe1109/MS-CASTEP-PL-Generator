# Manual Materials Studio submission

1. Open the intended Materials Studio project.
2. Create or select one project folder for one generated task.
3. Import both the generated `.xsd` and `.pl` from that same task directory.
   Do not import the PL alone.
4. Open the copied XSD and confirm that the structure is visible.
5. Open the PL and confirm that `$model` exactly matches the imported XSD name.
6. Press `Ctrl+F5` (`Run on Server`).
7. Select the desired Gateway and queue. The PL intentionally does not
   hard-code either one.
8. Confirm the requested core count in Script Job Control.
9. Record the Job ID and verify that it becomes `queued` or `running`.
10. After completion, confirm that `opt.xsd` and `report.txt` returned.
11. Check the PL output for:

    ```text
    RESULT status=completed
    ```

If Job Control says `Failed` but the CASTEP report contains
`Geometry optimization completed successfully`, inspect the PL output. An old
script may have attempted ordinary Perl `open()` on a Materials Studio virtual
path. Regenerate the package with this skill; do not discard a converged CASTEP
structure solely because the wrapper failed after the calculation.

`Server = Scripting` is expected for a PL driver. The PL internally calls
`Modules->CASTEP->GeometryOptimization->Run(...)`.
