{
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {}
          ]
        }
      },
      "name": "Disparador de programación",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1.2,
      "position": [
        -704,
        336
      ],
      "id": "fb2733a8-02f7-40fd-8ece-2c96e282855b"
    },
    {
      "parameters": {
        "documentId": {
          "__rl": true,
          "value": "1ofmDRz5vO_omJbsSy_98f6g4I_t-YtBEbKduczhV6lA",
          "mode": "list",
          "cachedResultName": "toytoons",
          "cachedResultUrl": "https://docs.google.com/spreadsheets/d/1ofmDRz5vO_omJbsSy_98f6g4I_t-YtBEbKduczhV6lA/edit?usp=drivesdk"
        },
        "sheetName": {
          "__rl": true,
          "value": "gid=0",
          "mode": "list",
          "cachedResultName": "Hoja 1",
          "cachedResultUrl": "https://docs.google.com/spreadsheets/d/1ofmDRz5vO_omJbsSy_98f6g4I_t-YtBEbKduczhV6lA/edit#gid=0"
        },
        "filtersUI": {
          "values": []
        },
        "options": {}
      },
      "name": "Obtener fila(s) en la hoja",
      "type": "n8n-nodes-base.googleSheets",
      "typeVersion": 4.5,
      "position": [
        -528,
        336
      ],
      "id": "7f1ad287-8e38-4a22-88ba-755878936200",
      "credentials": {
        "googleSheetsOAuth2Api": {
          "id": "8yr4F4ap72G8KURo",
          "name": "Google Sheets account"
        }
      }
    },
    {
      "parameters": {
        "promptType": "define",
        "text": "=Actúa como un compositor experto de canciones infantiles educativas y pegadizas para el canal ToyToons. Escribe una canción infantil completa y alegre sobre el siguiente tema: {{ $json.tema }}.\n\nLa canción debe ser larga, estructurada y tener el siguiente formato exacto:\n- Título de la canción\n- Estrofa 1 (4 líneas)\n- Coro (4 líneas, muy alegre y repetitivo)\n- Estrofa 2 (4 líneas)\n- Coro (4 líneas)\n- Estrofa 3 (4 líneas)\n- Coro final (4 líneas)\n- Cierre o despedida (2 líneas)\n\nNo incluyas saludos ni comentarios adicionales, entrega únicamente la letra de la canción estructurada."
      },
      "name": "Cadena básica de LLM",
      "type": "@n8n/n8n-nodes-langchain.chainLlm",
      "typeVersion": 1.4,
      "position": [
        -192,
        336
      ],
      "id": "3874efba-b9c6-4c5a-b2e0-afc5396ecb17"
    },
    {
      "parameters": {
        "url": "https://api.pexels.com/v1/videos/search?query=happy%20kids%20cartoon%20toys&per_page=1",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Authorization",
              "value": "7MG2eewyLnfL5DSAtpMFDQJl44nSx40aIZlz9kZSRzqketbbJAhdSjTM"
            }
          ]
        },
        "options": {
          "timeout": 120000
        }
      },
      "name": "pexels",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [
        688,
        496
      ],
      "id": "9ded7ade-bc01-4a4b-8038-05b9a0824d2e"
    },
    {
      "parameters": {
        "url": "={{ $json.download_link }}",
        "options": {
          "response": {
            "response": {
              "responseFormat": "file"
            }
          }
        }
      },
      "name": "DESCARGA DE VIDEO",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [
        1664,
        320
      ],
      "id": "9ff488f8-63f1-4dae-9cfc-faf1db8390d6"
    },
    {
      "parameters": {},
      "type": "n8n-nodes-base.limit",
      "typeVersion": 1,
      "position": [
        -352,
        336
      ],
      "id": "682c965b-13f2-4345-823c-f65064c99590",
      "name": "Limit"
    },
    {
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "id": "c77408d2-2809-4dc3-aca2-d619a44a5de4",
              "name": "videos[0].url",
              "value": "={{ $json.link }}",
              "type": "array"
            }
          ]
        },
        "options": {}
      },
      "type": "n8n-nodes-base.set",
      "typeVersion": 3.4,
      "position": [
        976,
        320
      ],
      "id": "180926f4-116a-4c4e-940a-7410d651d2c8",
      "name": "Edit Fields"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://api.cloudinary.com/v1_1/on3dlnbs/video/upload",
        "sendBody": true,
        "contentType": "multipart-form-data",
        "bodyParameters": {
          "parameters": [
            {
              "parameterType": "formBinaryData",
              "name": "file",
              "inputDataFieldName": "data"
            },
            {
              "name": "upload_preset",
              "value": "preset_toytoons"
            }
          ]
        },
        "options": {}
      },
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.4,
      "position": [
        1856,
        320
      ],
      "id": "dc2cc4ce-6ad6-4b9c-836d-6fd58b924c25",
      "name": "CLOUDINARY1"
    },
    {
      "parameters": {
        "options": {}
      },
      "type": "n8n-nodes-base.splitInBatches",
      "typeVersion": 3,
      "position": [
        512,
        336
      ],
      "id": "d94c69d9-d67f-44ac-b052-48c1de773512",
      "name": "Loop Over Items"
    },
    {
      "parameters": {
        "fieldsToAggregate": {
          "fieldToAggregate": [
            {
              "fieldToAggregate": "videos[0].video_files[0].link"
            }
          ]
        },
        "options": {}
      },
      "type": "n8n-nodes-base.aggregate",
      "typeVersion": 1,
      "position": [
        800,
        320
      ],
      "id": "867ae27a-3c52-4762-a5c8-508915fdd236",
      "name": "Aggregate"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://mi-render-video.onrender.com/generar-voz",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "text",
              "value": "={{ $json.text }}"
            },
            {
              "name": "voice",
              "value": "es-MX-DaliaNeural"
            }
          ]
        },
        "options": {
          "response": {
            "response": {
              "responseFormat": "file"
            }
          }
        }
      },
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.4,
      "position": [
        128,
        704
      ],
      "id": "c82770a1-9a51-46b3-9e95-bb3dd90c2470",
      "name": "GENERADOR AUDIO"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://mi-render-video.onrender.com/render-final",
        "sendBody": true,
        "contentType": "multipart-form-data",
        "bodyParameters": {
          "parameters": [
            {
              "name": "video_url",
              "value": "={{ $json.secure_url }}"
            },
            {
              "parameterType": "formBinaryData",
              "name": "audio",
              "inputDataFieldName": "={{ $('GENERADOR AUDIO').binary.data }}"
            }
          ]
        },
        "options": {}
      },
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.4,
      "position": [
        2288,
        320
      ],
      "id": "dfb99191-558a-4ca2-984c-a873e3791244",
      "name": "FFmpeg"
    },
    {
      "parameters": {
        "jsCode": "// Recogemos absolutamente todos los datos que vienen de cualquier nodo anterior en el flujo\nconst allItems = $input.all();\nlet urlsArray = [];\n\nfor (const item of allItems) {\n  // Buscamos recursivamente cualquier propiedad que contenga una URL de video\n  const searchValues = (obj) => {\n    if (!obj || typeof obj !== 'object') return;\n    for (const key in obj) {\n      const val = obj[key];\n      if (typeof val === 'string' && (val.startsWith('http://') || val.startsWith('https://')) && (val.includes('.mp4') || val.includes('pexels'))) {\n        urlsArray.push(val);\n      } else if (typeof val === 'object') {\n        searchValues(val);\n      }\n    }\n  };\n  searchValues(item.json);\n}\n\n// Limpiamos duplicados\nconst uniqueUrls = [...new Set(urlsArray)];\n\n// Devolvemos el array limpio para el nodo HTTP\nreturn [{ json: { urls: uniqueUrls } }];"
      },
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [
        1136,
        320
      ],
      "id": "6e82af98-40f1-4e55-97f9-c181bf25d10c",
      "name": "Code in JavaScript2"
    },
    {
      "parameters": {
        "jsCode": "// Tomamos el resultado del LLM o definimos un tema base infantil\nconst inputData = $input.item.json;\nconst temaBase = \"happy kids playing cartoon toys educational\";\n\n// Generamos 8 escenas variadas para cubrir los 2 minutos de video\nconst queries = [\n  \"happy kids playing colorful toys\",\n  \"children learning numbers letters preschool\",\n  \"cute cartoon animation kids smiling\",\n  \"toddlers playing blocks educational room\",\n  \"kids dancing and singing joyfully\",\n  \"bright colorful toys spinning playful\",\n  \"happy children preschool classroom fun\",\n  \"cute kids playing together smiling\"\n];\n\n// Creamos la lista de elementos (items) para que el Loop los procese uno por uno\nreturn queries.map((q, index) => {\n  return {\n    json: {\n      escena_numero: index + 1,\n      query_busqueda: q\n    }\n  };\n});"
      },
      "name": "Código en JavaScript1",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [
        304,
        336
      ],
      "id": "3816fd6f-81ab-457b-9826-7b9b37525c2b"
    },
    {
      "parameters": {
        "jsCode": "const item = $input.item.json;\nlet targetUrl = \"\";\n\n// Función recursiva para buscar cualquier string que sea una URL de video mp4\nfunction findUrl(obj) {\n  if (!obj) return;\n  if (typeof obj === 'string' && obj.startsWith('http') && obj.includes('.mp4')) {\n    targetUrl = obj;\n    return;\n  }\n  if (typeof obj === 'object') {\n    for (let key in obj) {\n      findUrl(obj[key]);\n      if (targetUrl) return;\n    }\n  } else if (typeof obj === 'string' && obj.includes('{')) {\n    try {\n      findUrl(JSON.parse(obj));\n    } catch (e) {}\n  }\n}\n\nfindUrl(item);\n\n// Si por alguna razón no la encuentra en profundidad, revisamos campos comunes\nif (!targetUrl && item.URL && item.URL.urls) {\n  targetUrl = item.URL.urls[0];\n}\n\nreturn { json: { download_link: targetUrl } };"
      },
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [
        1488,
        320
      ],
      "id": "1cc78f1c-4efc-4964-addc-c8c0f30c9c09",
      "name": "Code in JavaScript3"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "=https://mi-render-video.onrender.com/unir-videos",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "urls",
              "value": "={   \"urls\": {{ JSON.stringify($json.urls) }} }"
            }
          ]
        },
        "options": {}
      },
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.4,
      "position": [
        1312,
        320
      ],
      "id": "07d79fd3-185b-4b67-85e1-71b47261551f",
      "name": "mi-render"
    },
    {
      "parameters": {
        "model": "qwen/qwen3.6-27b",
        "options": {}
      },
      "type": "@n8n/n8n-nodes-langchain.lmChatGroq",
      "typeVersion": 1,
      "position": [
        -192,
        544
      ],
      "id": "c9f59673-43cf-4591-81e9-6dcb74012b03",
      "name": "Groq Chat Model",
      "credentials": {
        "groqApi": {
          "id": "Y94zTBmZ1jw3wAMP",
          "name": "Groq account"
        }
      }
    },
    {
      "parameters": {},
      "type": "n8n-nodes-base.merge",
      "typeVersion": 3.2,
      "position": [
        2096,
        704
      ],
      "id": "e3bb5661-fbe9-4299-a668-4f1f22344bd5",
      "name": "Merge"
    }
  ],
  "connections": {
    "Disparador de programación": {
      "main": [
        [
          {
            "node": "Obtener fila(s) en la hoja",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Obtener fila(s) en la hoja": {
      "main": [
        [
          {
            "node": "Limit",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Cadena básica de LLM": {
      "main": [
        [
          {
            "node": "GENERADOR AUDIO",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "pexels": {
      "main": [
        [
          {
            "node": "Loop Over Items",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "DESCARGA DE VIDEO": {
      "main": [
        [
          {
            "node": "CLOUDINARY1",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Limit": {
      "main": [
        [
          {
            "node": "Cadena básica de LLM",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Edit Fields": {
      "main": [
        [
          {
            "node": "Code in JavaScript2",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "CLOUDINARY1": {
      "main": [
        [
          {
            "node": "Merge",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Loop Over Items": {
      "main": [
        [
          {
            "node": "Aggregate",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "pexels",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Aggregate": {
      "main": [
        [
          {
            "node": "Edit Fields",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "GENERADOR AUDIO": {
      "main": [
        [
          {
            "node": "Merge",
            "type": "main",
            "index": 1
          },
          {
            "node": "Código en JavaScript1",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Code in JavaScript2": {
      "main": [
        [
          {
            "node": "mi-render",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Código en JavaScript1": {
      "main": [
        [
          {
            "node": "Loop Over Items",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Code in JavaScript3": {
      "main": [
        [
          {
            "node": "DESCARGA DE VIDEO",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "mi-render": {
      "main": [
        [
          {
            "node": "Code in JavaScript3",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Groq Chat Model": {
      "ai_languageModel": [
        [
          {
            "node": "Cadena básica de LLM",
            "type": "ai_languageModel",
            "index": 0
          }
        ]
      ]
    },
    "Merge": {
      "main": [
        [
          {
            "node": "FFmpeg",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "pinData": {},
  "meta": {
    "instanceId": "2b4d1e2ae4114a5fb9eb99ad73dde707de0bec48b00d32672dc2220ed1b5c448"
  }
}
