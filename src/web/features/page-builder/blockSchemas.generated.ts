export const blockTypes = {
  hero: {
    title: "Hero",
    schema: {
      type: "object",
      properties: {
        title: {
          type: "string",
          title: "Title",
          maxLength: 200,
          default: "",
          "x-nonblank": true,
          "x-widget": "input",
          "x-create-default": "New hero",
        },
        subtitle: {
          type: "string",
          title: "Subtitle",
          maxLength: 400,
          default: "",
          "x-nonblank": false,
          "x-widget": "input",
          "x-create-default": null,
        },
        cta_label: {
          type: "string",
          title: "CTA label",
          maxLength: 60,
          default: "",
          "x-nonblank": false,
          "x-widget": "input",
          "x-create-default": null,
        },
        cta_href: {
          type: "string",
          title: "CTA link",
          maxLength: 2000,
          default: "",
          "x-nonblank": false,
          "x-widget": "input",
          "x-create-default": null,
        },
      },
      additionalProperties: true,
    },
  },
  cta: {
    title: "Call to action",
    schema: {
      type: "object",
      properties: {
        label: {
          type: "string",
          title: "Label",
          maxLength: 60,
          default: "",
          "x-nonblank": true,
          "x-widget": "input",
          "x-create-default": "Learn more",
        },
        href: {
          type: "string",
          title: "Link",
          maxLength: 2000,
          default: "",
          "x-nonblank": true,
          "x-widget": "input",
          "x-create-default": "/",
        },
      },
      additionalProperties: true,
    },
  },
  rich_text: {
    title: "Rich text",
    schema: {
      type: "object",
      properties: {
        html: {
          type: "string",
          title: "HTML (sanitized on save)",
          maxLength: 20000,
          default: "",
          "x-nonblank": true,
          "x-widget": "textarea",
          "x-create-default": "<p>New content</p>",
        },
      },
      additionalProperties: true,
    },
  },
  faq: {
    title: "FAQ",
    schema: {
      type: "object",
      properties: {
        items: {
          type: "array",
          title: "Items",
          maxItems: 20,
          default: [],
          items: {
            type: "object",
            properties: {
              question: {
                type: "string",
                title: "question",
                maxLength: 500,
                default: "",
                "x-nonblank": false,
                "x-widget": "input",
                "x-create-default": null,
              },
              answer: {
                type: "string",
                title: "answer",
                maxLength: 500,
                default: "",
                "x-nonblank": false,
                "x-widget": "input",
                "x-create-default": null,
              },
            },
            additionalProperties: false,
          },
        },
      },
      additionalProperties: true,
    },
  },
  sponsors: {
    title: "Sponsors",
    schema: {
      type: "object",
      properties: {
        items: {
          type: "array",
          title: "Items",
          maxItems: 20,
          default: [],
          items: {
            type: "object",
            properties: {
              name: {
                type: "string",
                title: "name",
                maxLength: 500,
                default: "",
                "x-nonblank": false,
                "x-widget": "input",
                "x-create-default": null,
              },
              url: {
                type: "string",
                title: "url",
                maxLength: 500,
                default: "",
                "x-nonblank": false,
                "x-widget": "input",
                "x-create-default": null,
              },
            },
            additionalProperties: false,
          },
        },
      },
      additionalProperties: true,
    },
  },
  resources: {
    title: "Resources",
    schema: {
      type: "object",
      properties: {
        items: {
          type: "array",
          title: "Items",
          maxItems: 20,
          default: [],
          items: {
            type: "object",
            properties: {
              label: {
                type: "string",
                title: "label",
                maxLength: 500,
                default: "",
                "x-nonblank": false,
                "x-widget": "input",
                "x-create-default": null,
              },
              url: {
                type: "string",
                title: "url",
                maxLength: 500,
                default: "",
                "x-nonblank": false,
                "x-widget": "input",
                "x-create-default": null,
              },
            },
            additionalProperties: false,
          },
        },
      },
      additionalProperties: true,
    },
  },
  gallery: {
    title: "Gallery preview (live)",
    schema: {
      type: "object",
      properties: {
        limit: {
          type: "integer",
          title: "Projects to preview",
          minimum: 1,
          maximum: 24,
          default: 6,
        },
      },
      additionalProperties: true,
    },
  },
  tracks: {
    title: "Tracks (live)",
    schema: {
      type: "object",
      properties: {},
      additionalProperties: false,
    },
  },
  prizes: {
    title: "Prizes (live)",
    schema: {
      type: "object",
      properties: {},
      additionalProperties: false,
    },
  },
  schedule: {
    title: "Schedule (live)",
    schema: {
      type: "object",
      properties: {},
      additionalProperties: false,
    },
  },
  results: {
    title: "Results (live)",
    schema: {
      type: "object",
      properties: {},
      additionalProperties: false,
    },
  },
  announcements: {
    title: "Announcements (live)",
    schema: {
      type: "object",
      properties: {},
      additionalProperties: false,
    },
  },
} as const;
