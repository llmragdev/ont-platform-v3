# API 초안

## 1. Ontology Schema

```text
GET    /api/ontology/schema
PUT    /api/ontology/schema
POST   /api/ontology/validate
POST   /api/ontology/publish
```

## 2. Object Types

```text
GET    /api/ontology/object-types
POST   /api/ontology/object-types
GET    /api/ontology/object-types/{type_name}
PUT    /api/ontology/object-types/{type_name}
```

## 3. Relationship Types

```text
GET    /api/ontology/relationship-types
POST   /api/ontology/relationship-types
GET    /api/ontology/relationship-types/{type_name}
PUT    /api/ontology/relationship-types/{type_name}
```

## 4. Objects

```text
GET    /api/ontology/objects?type=Customer
POST   /api/ontology/objects
GET    /api/ontology/objects/{object_id}
GET    /api/ontology/objects/{object_id}/context
PUT    /api/ontology/objects/{object_id}
DELETE /api/ontology/objects/{object_id}
```

## 5. Relationships

```text
GET    /api/ontology/relationships?type=PLACED_ORDER
POST   /api/ontology/relationships
DELETE /api/ontology/relationships/{relationship_id}
```

## 6. Actions

```text
GET    /api/ontology/actions
POST   /api/ontology/actions
POST   /api/actions/{action_name}/execute
```

## 7. AI

```text
POST   /api/ask
POST   /api/search
```

AI 응답은 `ontology_context`, `evidence`, `available_actions`, `trace`를 포함한다.

