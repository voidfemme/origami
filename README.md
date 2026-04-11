## Classes to manage individual themes:

- OrigamiConfig
  - config path: Path
  - available rices: list[Rice]
  - common rice: [Rice]

  - Rice
    - theme-path: Path
    - available components: list[Component] # Each app config is considered a
      component
    - apply-theme()

    - Component
      - component-path: Path
      - apply-component()
      - verify-paths() # do the _source_ files exist in $CORE?
      - check-health() # do the _symlinks_ exist at their expected target
        locations? Do they point to the right place?
      - BuildConfig
        - build-file: Path
        - parse-build()
        - validate-config()
