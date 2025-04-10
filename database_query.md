### delete user
    DELETE FROM users WHERE id = 'f7a632b0-e853-4376-99c6-e7c2160398bc';

### Deparment Create
    CREATE TABLE departments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL,
        department_name VARCHAR(255) NOT NULL,
        description TEXT,
        parent_department_id UUID NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        CONSTRAINT uq_user_department_name UNIQUE (user_id, department_name),
        CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        CONSTRAINT fk_parent_department FOREIGN KEY (parent_department_id) REFERENCES parent_departments(id) ON DELETE CASCADE
    );

    ALTER TABLE departments 
    ADD CONSTRAINT uq_user_department_name UNIQUE (user_id, department_name);




### Add Foregiven Key
    ALTER TABLE departments 
    ADD COLUMN parent_department_id UUID;
    
    ALTER TABLE departments 
    ADD CONSTRAINT departments_parent_department_id_fkey 
    FOREIGN KEY (parent_department_id) 
    REFERENCES parent_departments(id) 
    ON DELETE CASCADE;
